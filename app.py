import os
import time
from flask import Flask, render_template_string, request, send_from_directory, jsonify
from checker import check_robots, check_ucp_config, check_homepage
from scorer import calculate_score
from reporter import generate_report, generate_pdf
from utils import normalize_url
from logger import logger

app = Flask(__name__)
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# HTML Template for the Web UI
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UCP Compliance Scanner</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .loader {
            border: 3px solid #f3f4f6;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen flex flex-col items-center pt-20">

    <div class="w-full max-w-2xl px-6">
        <div class="text-center mb-10">
            <h1 class="text-4xl font-extrabold tracking-tight text-gray-900 mb-2">UCP <span class="text-blue-600">Scanner</span></h1>
            <p class="text-gray-500">Universal Content Protocol Compliance Audit</p>
        </div>

        <div class="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
            <form id="scanForm" class="space-y-6">
                <div>
                    <label for="url" class="block text-sm font-medium text-gray-700 mb-2">Website URL</label>
                    <div class="relative rounded-md shadow-sm">
                        <input type="text" name="url" id="url" 
                               class="block w-full pl-4 pr-12 py-3 border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-base" 
                               placeholder="https://example.com" required>
                    </div>
                </div>

                <button type="submit" id="submitBtn" 
                        class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                    <span>Run Compliance Scan</span>
                </button>
            </form>
            
            <div id="loading" class="hidden mt-6 text-center">
                <div class="flex flex-col items-center justify-center">
                    <div class="loader mb-3"></div>
                    <p class="text-sm text-gray-500">Analyzing endpoints...</p>
                </div>
            </div>
            
            <div id="error" class="hidden mt-6 p-4 bg-red-50 text-red-700 rounded-lg text-sm"></div>
        </div>
    </div>

    <!-- Results Container (Hidden initially) -->
    <div id="resultsArea" class="w-full max-w-4xl px-6 mt-10 mb-20 hidden">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold text-gray-800">Scan Report</h2>
            <a id="downloadLink" href="#" target="_blank" 
               class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                Download PDF
            </a>
        </div>
        
        <div id="reportContent" class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden min-h-[500px]">
            <!-- Iframe to preview HTML report -->
            <iframe id="reportFrame" class="w-full h-[800px] border-none"></iframe>
        </div>
    </div>

    <script>
        const form = document.getElementById('scanForm');
        const loading = document.getElementById('loading');
        const submitBtn = document.getElementById('submitBtn');
        const errorDiv = document.getElementById('error');
        const resultsArea = document.getElementById('resultsArea');
        const reportFrame = document.getElementById('reportFrame');
        const downloadLink = document.getElementById('downloadLink');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // UI State: Loading
            loading.classList.remove('hidden');
            errorDiv.classList.add('hidden');
            resultsArea.classList.add('hidden');
            submitBtn.disabled = true;
            submitBtn.querySelector('span').textContent = "Scanning...";
            
            const url = document.getElementById('url').value;
            
            try {
                // Use relative path for subpath deployment support
                const response = await fetch('scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Scan failed');
                }
                
                // Success - use relative paths
                resultsArea.classList.remove('hidden');
                reportFrame.src = `view/${data.html_file}`;
                downloadLink.href = `download/${data.pdf_file}`;
                
            } catch (err) {
                errorDiv.textContent = err.message;
                errorDiv.classList.remove('hidden');
            } finally {
                loading.classList.add('hidden');
                submitBtn.disabled = false;
                submitBtn.querySelector('span').textContent = "Run Compliance Scan";
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(INDEX_HTML)

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    target_url = data.get('url')
    
    if not target_url:
        return jsonify({'error': 'URL is required'}), 400
        
    try:
        # 1. Normalize
        raw_url, base_url, host, tld, is_us_guess = normalize_url(target_url)
        if not base_url:
            return jsonify({'error': 'Invalid URL format'}), 400
            
        logger.info(f"Web Scan initiated for {base_url}")
        
        # 2. Check
        robots_res = check_robots(base_url)
        ucp_res = check_ucp_config(base_url)
        home_res = check_homepage(base_url)
        
        # 3. Score
        result = calculate_score(base_url, host, is_us_guess, robots_res, ucp_res, home_res)
        
        # 4. Generate Files
        sanitized_host = host.replace('.', '_')
        timestamp = int(time.time())
        filename_base = f"UCP_Report_{sanitized_host}_{timestamp}"
        
        output_html = os.path.join(OUTPUT_DIR, f"{filename_base}.html")
        output_pdf = os.path.join(OUTPUT_DIR, f"{filename_base}.pdf")
        
        html_content = generate_report(result)
        
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        try:
            generate_pdf(output_html, output_pdf)
        except Exception as e:
            logger.error(f"PDF Gen failed key web request: {e}")
            # Continue without PDF if fails (client handles?)
            
        return jsonify({
            'status': 'success',
            'html_file': f"{filename_base}.html",
            'pdf_file': f"{filename_base}.pdf",
            'score': result['weightedAverage']
        })

    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route('/view/<filename>')
def view_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
