"""
Swagger UI — served at /api/docs
Loads openapi.yaml from /docs/openapi.yaml
"""

import os
from flask import Blueprint, send_from_directory, jsonify
import yaml

swagger_bp = Blueprint('swagger', __name__, url_prefix='/api/docs')

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')


@swagger_bp.route('', methods=['GET'])
@swagger_bp.route('/', methods=['GET'])
def swagger_ui():
    """Serve the Swagger UI HTML page."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NyumbaLink API Docs</title>
  <link rel="stylesheet" type="text/css"
        href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; }
    #swagger-ui .topbar { background: #15803d; }
    #swagger-ui .topbar-wrapper img { content: url('data:image/svg+xml,<svg></svg>'); }
    #swagger-ui .topbar-wrapper::after { content: "NyumbaLink API"; color: white; font-size: 1.2rem; font-weight: 700; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = () => {
      SwaggerUIBundle({
        url: '/api/docs/openapi.yaml',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        plugins: [SwaggerUIBundle.plugins.DownloadUrl],
        layout: 'StandaloneLayout',
        persistAuthorization: true,
      });
    };
  </script>
</body>
</html>"""
    from flask import Response
    return Response(html, mimetype='text/html')


@swagger_bp.route('/openapi.yaml')
def openapi_yaml():
    """Serve the raw OpenAPI YAML spec."""
    return send_from_directory(DOCS_DIR, 'openapi.yaml', mimetype='application/yaml')


@swagger_bp.route('/openapi.json')
def openapi_json():
    """Serve the OpenAPI spec as JSON (for tooling compatibility)."""
    spec_path = os.path.join(DOCS_DIR, 'openapi.yaml')
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)
