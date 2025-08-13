import json
import os
import sys
import requests
import yaml
import base64
import re
from urllib.parse import urlparse
from jsonschema import validate, ValidationError
import jsonref
import pandas as pd
from jsonschema import Draft7Validator

def load_files(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        test_log = json.load(f)
    return test_log

def normalize_path(uri, openapi_paths):
    path = urlparse(uri).path
    parts = path.strip("/").split("/")
    
    for i, part in enumerate(parts):
        if re.fullmatch(r"v\d+", part):
            parts = parts[i + 1:]
            break

    for openapi_path in openapi_paths:
        candidate_parts = openapi_path.strip("/").split("/")
        if len(candidate_parts) != len(parts):
            continue
        result_parts = []
        matched = True
        for spec_seg, uri_seg in zip(candidate_parts, parts):
            if spec_seg.startswith("{"):
                result_parts.append(spec_seg)
            elif spec_seg == uri_seg:
                result_parts.append(uri_seg)
            else:
                matched = False
                break
        if matched:
            return "/" + "/".join(result_parts)

    return "/" + "/".join(parts)

def find_matching_path(openapi_paths, normalized_uri, method):
    for path, methods in openapi_paths.items():
        if path == normalized_uri and method.lower() in methods:
            return path, methods[method.lower()]
    return None, None

def validate_payload(payload, schema):
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if not errors:
        return "PASS", []
    return "FAIL", [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]

def decode_jwt(jwt):
    try:
        parts = jwt.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return None

def run_jwt_aware_validation(log_path, openapi):
    test_log = load_files(log_path)
    summary = []
    openapi_paths = openapi.get("paths", {})
    print(f"Loaded OpenAPI with {len(openapi_paths)} paths.")
    # Track last request for context
    last_request_uri = None
    last_request_method = None
    testName  = test_log.get("testInfo", {}).get("testName")
    print(f"Processing test: {testName}")
    for item in test_log.get("results", []):
        request_uri = item.get("request_uri")
        method = item.get("request_method")
        request_body = item.get("request_body")
        response_body = item.get("response_body")
        id = item.get("_id")
        src = item.get("src")
        msg = item.get("msg")
        http = item.get("http")

        if request_uri and method:
            last_request_uri = request_uri
            last_request_method = method.upper()

        if not last_request_uri or (not request_body and not response_body):
            continue
      
        normalized_uri = normalize_path(last_request_uri, openapi_paths)
        matched_path, operation = find_matching_path(openapi_paths, normalized_uri, last_request_method)
        if not matched_path:
            continue

        # Validate request body
        if request_body and isinstance(request_body, str):
            decoded_req = decode_jwt(request_body)
            if decoded_req and "requestBody" in operation:
                schema = operation["requestBody"]["content"].get("application/jwt", {}).get("schema", {})
                payload = decoded_req
                status, error = validate_payload(payload, schema)
                result = {
                    "test_name": testName,
                    "id": id,
                    "request_uri": normalized_uri,
                    "request_method": last_request_method,
                    "status": status,
                    "src": src,
                    "msg": msg,
                    "http": http
                }
                if status == "FAIL":
                    result["error"] = error
                summary.append(result)

        # Validate response body
        if response_body and isinstance(response_body, str):
            decoded_resp = decode_jwt(response_body)
            if decoded_resp and "responses" in operation:
                for response in operation["responses"].values():
                    content = response.get("content", {})
                    if "application/jwt" in content:
                        schema = content["application/jwt"].get("schema", {})
                        payload = decoded_resp
                        # if "data" in schema.get("properties", {}):
                        #     schema = schema["properties"]["data"]
                        status, error = validate_payload(payload, schema)
                        result = {
                            "test_name": testName,
                            "id": id,
                            "request_uri": normalized_uri,
                            "request_method": last_request_method,
                            "status": status,
                            "src": src,
                            "msg": msg,
                            "http": http
                            
                        }
                        if status == "FAIL":
                            result["error"] = error
                        summary.append(result)
                        break

    return summary

def get_all_json_files(directory):
    """Retorna uma lista com todos os arquivos .json do diretório especificado."""
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json") and os.path.isfile(os.path.join(directory, f))
    ]

def get_openapi_from_url(url):
    """Obtém o OpenAPI de uma URL e retorna como um dicionário."""
    response = requests.get(url)
    if response.status_code == 200:
        body = response.text
        raw_spec = yaml.safe_load(body)
        openapi = jsonref.JsonRef.replace_refs(raw_spec)
        return openapi
    else:
        raise Exception(f"Erro ao buscar OpenAPI: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validate_test.py <url_raw_no_formato_yml>")
        sys.exit(1)

    scenarios_path = "cenarios"
    url_openApi = sys.argv[1]
    print(f"Validando arquivos no diretório: {scenarios_path}")     
    cenariosFiles = get_all_json_files(scenarios_path)
    
    print(f"Obtendo OpenAPI de: {url_openApi}")
    obj_api_openapi = get_openapi_from_url(url_openApi)
    
    outputResult = []
    for file in cenariosFiles:
        print(f"Validando arquivo: {file}")
        output = run_jwt_aware_validation(file, obj_api_openapi)
        outputResult.extend(output)
        
    # Output to console as JSON
    print(json.dumps(outputResult, indent=2, ensure_ascii=False))

    # Save to CSV
    df = pd.DataFrame(outputResult)
    df.to_csv("validation_results.csv", index=False, encoding="utf-8")
    print("\n✅ CSV file written to: validation_results.csv")
