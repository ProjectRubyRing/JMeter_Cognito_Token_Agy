#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAPI 3.0 / 3.1 / Swagger 2.0 to JMeter 5.6.3 Test Plan (.jmx) Generator
Features:
- Full support for JSON and YAML OpenAPI specifications.
- Minimal Thread Group configuration (1 thread, 1 loop, 1s ramp-up) for single request verification.
- Default endpoint: http://localhost:8080.
- Automatic mock test data generation based on OpenAPI data types and schemas.
- Fixed header: X-API-KEY with initial default 'XXXXXXXXXXXX'.
- Premise: Acquires AWS Cognito Access Token first (Client Credentials flow) and passes
  'Authorization: Bearer ${cognito_access_token}' to subsequent API Gateway calls.
- Dual extractors: JSON Extractor and Regular Expression Extractor for access_token.
- Generates GUI-compatible View Results Tree and Summary Report listeners writing to results.jtl and jmeter.log.
"""

import sys
import os
import json
import random
import string
import uuid
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# YAML loading with fallback
HAVE_YAML = False
try:
    import ruamel.yaml
    yaml_loader = ruamel.yaml.YAML(typ='safe')
    HAVE_YAML = "ruamel"
except ImportError:
    try:
        import yaml
        HAVE_YAML = "pyyaml"
    except ImportError:
        HAVE_YAML = False


def load_openapi_spec(file_path):
    """Loads OpenAPI specification from JSON or YAML file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"OpenAPI file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try parsing as JSON first
    try:
        return json.loads(content)
    except Exception:
        pass

    # If JSON fails, try YAML
    if HAVE_YAML == "ruamel":
        return yaml_loader.load(content)
    elif HAVE_YAML == "pyyaml":
        return yaml.safe_load(content)
    else:
        # Simple fallback for YAML if neither is installed: try minimal parsing or error
        raise RuntimeError(
            "YAML parser (ruamel.yaml or PyYAML) is not installed. "
            "Please install ruamel.yaml or PyYAML, or provide the OpenAPI spec in JSON format."
        )


class MockDataGenerator:
    """Generates realistic mock data based on OpenAPI schema definitions."""

    def __init__(self, root_spec):
        self.root_spec = root_spec

    def resolve_ref(self, ref_str):
        """Resolves a local $ref pointer (e.g. #/components/schemas/User)."""
        if not ref_str or not ref_str.startswith("#/"):
            return {}
        parts = ref_str.lstrip("#/").split("/")
        curr = self.root_spec
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return {}
        return curr

    def generate_value(self, schema, depth=0):
        """Recursively generates mock value for a given schema."""
        if depth > 5:
            return "nested_max_depth"

        if not schema or not isinstance(schema, dict):
            return "sample_value"

        if "$ref" in schema:
            resolved = self.resolve_ref(schema["$ref"])
            return self.generate_value(resolved, depth + 1)

        # Check for example or default
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        if "enum" in schema and schema["enum"]:
            return random.choice(schema["enum"])

        data_type = schema.get("type", "string")
        data_format = schema.get("format", "")

        if data_type == "string":
            if data_format == "uuid":
                return str(uuid.uuid4())
            elif data_format == "email":
                rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
                return f"test_perf_{rnd}@example.com"
            elif data_format in ("date", "date-time"):
                return "2026-10-01T00:00:00Z"
            elif data_format == "uri":
                return "https://api.example.com/resource"
            else:
                rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
                return f"str_{rnd}"

        elif data_type in ("integer", "int"):
            min_val = schema.get("minimum", 1)
            max_val = schema.get("maximum", 1000)
            if min_val > max_val:
                min_val, max_val = 1, 100
            return random.randint(int(min_val), min(int(max_val), 1000))

        elif data_type in ("number", "float", "double"):
            min_val = float(schema.get("minimum", 1.0))
            max_val = float(schema.get("maximum", 500.0))
            return round(random.uniform(min_val, max_val), 2)

        elif data_type == "boolean":
            return random.choice([True, False])

        elif data_type == "array":
            items_schema = schema.get("items", {})
            return [self.generate_value(items_schema, depth + 1)]

        elif data_type == "object" or "properties" in schema:
            obj = {}
            props = schema.get("properties", {})
            for prop_name, prop_schema in props.items():
                obj[prop_name] = self.generate_value(prop_schema, depth + 1)
            return obj

        return "mock_val"


class JMeterScenarioBuilder:
    """Constructs JMeter 5.6.3 XML Test Plan."""

    def __init__(self, spec, target_host="localhost", target_port="8080", target_protocol="http",
                 api_key="XXXXXXXXXXXX", cognito_token_url="https://auth.example.com/oauth2/token",
                 cognito_client_id="your_cognito_client_id", cognito_client_secret="your_cognito_client_secret",
                 cognito_scope="api/read api/write", jtl_path="results.jtl", log_path="jmeter.log"):
        self.spec = spec
        self.target_host = target_host
        self.target_port = target_port
        self.target_protocol = target_protocol
        self.api_key = api_key
        self.cognito_token_url = cognito_token_url
        self.cognito_client_id = cognito_client_id
        self.cognito_client_secret = cognito_client_secret
        self.cognito_scope = cognito_scope
        self.jtl_path = jtl_path
        self.log_path = log_path
        self.mock_gen = MockDataGenerator(spec)

    def _add_string_prop(self, parent, name, value):
        el = ET.SubElement(parent, "stringProp", {"name": name})
        el.text = str(value)
        return el

    def _add_bool_prop(self, parent, name, value):
        el = ET.SubElement(parent, "boolProp", {"name": name})
        el.text = "true" if value else "false"
        return el

    def _add_int_prop(self, parent, name, value):
        el = ET.SubElement(parent, "intProp", {"name": name})
        el.text = str(value)
        return el

    def _add_long_prop(self, parent, name, value):
        el = ET.SubElement(parent, "longProp", {"name": name})
        el.text = str(value)
        return el

    def build_jmx(self):
        """Generates the full JMeter 5.6.3 XML tree."""
        root = ET.Element("jmeterTestPlan", {
            "version": "1.2",
            "properties": "5.0",
            "jmeter": "5.6.3"
        })
        root_hash = ET.SubElement(root, "hashTree")

        # 1. TestPlan Element
        test_plan = ET.SubElement(root_hash, "TestPlan", {
            "guiclass": "TestPlanGui",
            "testclass": "TestPlan",
            "testname": f"OpenAPI Test Plan - {self.spec.get('info', {}).get('title', 'API Test')}",
            "enabled": "true"
        })
        self._add_string_prop(test_plan, "TestPlan.comments", "Auto-generated JMeter 5.6.3 scenario with AWS Cognito and API Gateway integration")
        self._add_bool_prop(test_plan, "TestPlan.functional_mode", False)
        self._add_bool_prop(test_plan, "TestPlan.tearDown_on_shutdown", True)
        self._add_bool_prop(test_plan, "TestPlan.serialize_threadgroups", False)
        ET.SubElement(test_plan, "elementProp", {
            "name": "TestPlan.user_defined_variables",
            "elementType": "Arguments",
            "guiclass": "ArgumentsPanel",
            "testclass": "Arguments",
            "testname": "User Defined Variables",
            "enabled": "true"
        })

        test_plan_hash = ET.SubElement(root_hash, "hashTree")

        # 2. User Defined Variables (Arguments)
        udv = ET.SubElement(test_plan_hash, "Arguments", {
            "guiclass": "ArgumentsPanel",
            "testclass": "Arguments",
            "testname": "Global Scenario Config",
            "enabled": "true"
        })
        collection_prop = ET.SubElement(udv, "collectionProp", {"name": "Arguments.arguments"})
        variables = [
            ("TARGET_HOST", self.target_host, "Target API Server Host"),
            ("TARGET_PORT", str(self.target_port), "Target API Server Port"),
            ("TARGET_PROTOCOL", self.target_protocol, "Protocol (http or https)"),
            ("API_KEY", self.api_key, "Fixed API Gateway X-API-KEY"),
            ("COGNITO_TOKEN_URL", self.cognito_token_url, "Cognito OAuth2 Token Endpoint"),
            ("COGNITO_CLIENT_ID", self.cognito_client_id, "Cognito App Client ID"),
            ("COGNITO_CLIENT_SECRET", self.cognito_client_secret, "Cognito App Client Secret"),
            ("COGNITO_SCOPE", self.cognito_scope, "OAuth2 Scopes"),
            ("JTL_PATH", self.jtl_path, "JTL Result Output File Path"),
            ("LOG_PATH", self.log_path, "Log Output File Path"),
        ]
        for var_name, var_val, var_desc in variables:
            arg = ET.SubElement(collection_prop, "elementProp", {"name": var_name, "elementType": "Argument"})
            self._add_string_prop(arg, "Argument.name", var_name)
            self._add_string_prop(arg, "Argument.value", var_val)
            self._add_string_prop(arg, "Argument.metadata", "=")
            self._add_string_prop(arg, "Argument.desc", var_desc)

        ET.SubElement(test_plan_hash, "hashTree")

        # 3. HTTP Header Manager (Global)
        header_mgr = ET.SubElement(test_plan_hash, "HeaderManager", {
            "guiclass": "HeaderPanel",
            "testclass": "HeaderManager",
            "testname": "Global HTTP Header Manager",
            "enabled": "true"
        })
        h_coll = ET.SubElement(header_mgr, "collectionProp", {"name": "HeaderManager.headers"})
        global_headers = [
            ("X-API-KEY", "${API_KEY}"),
            ("Authorization", "Bearer ${cognito_access_token}"),
            ("Content-Type", "application/json"),
            ("Accept", "application/json")
        ]
        for h_name, h_val in global_headers:
            h_el = ET.SubElement(h_coll, "elementProp", {"name": "", "elementType": "Header"})
            self._add_string_prop(h_el, "Header.name", h_name)
            self._add_string_prop(h_el, "Header.value", h_val)

        ET.SubElement(test_plan_hash, "hashTree")

        # 4. Minimal Thread Group (1 thread, 1 loop, 1s ramp-up)
        thread_group = ET.SubElement(test_plan_hash, "ThreadGroup", {
            "guiclass": "ThreadGroupGui",
            "testclass": "ThreadGroup",
            "testname": "OpenAPI API Verification Thread Group",
            "enabled": "true"
        })
        self._add_string_prop(thread_group, "ThreadGroup.on_sample_error", "continue")
        
        loop_ctrl = ET.SubElement(thread_group, "elementProp", {
            "name": "ThreadGroup.main_controller",
            "elementType": "LoopController",
            "guiclass": "LoopControlPanel",
            "testclass": "LoopController",
            "testname": "Loop Controller",
            "enabled": "true"
        })
        self._add_bool_prop(loop_ctrl, "LoopController.continue_forever", False)
        self._add_int_prop(loop_ctrl, "LoopController.loops", 1)

        self._add_int_prop(thread_group, "ThreadGroup.num_threads", 1)
        self._add_int_prop(thread_group, "ThreadGroup.ramp_time", 1)
        self._add_bool_prop(thread_group, "ThreadGroup.delayedStart", False)
        self._add_bool_prop(thread_group, "ThreadGroup.scheduler", False)

        tg_hash = ET.SubElement(test_plan_hash, "hashTree")

        # 5. Cognito Token Acquisition Request inside Once Only Controller (Token Reuse Pattern)
        once_ctrl = ET.SubElement(tg_hash, "OnceOnlyController", {
            "guiclass": "OnceOnlyControllerGui",
            "testclass": "OnceOnlyController",
            "testname": "Once Only - Cognito Authentication",
            "enabled": "true"
        })
        once_hash = ET.SubElement(tg_hash, "hashTree")

        # 5.1 HTTP Sampler: Cognito Token Request
        cognito_sampler = ET.SubElement(once_hash, "HTTPSamplerProxy", {
            "guiclass": "HttpTestSampleGui",
            "testclass": "HTTPSamplerProxy",
            "testname": "00_Cognito_Token_Acquisition",
            "enabled": "true"
        })
        self._add_bool_prop(cognito_sampler, "HTTPSampler.postBodyRaw", False)
        self._add_string_prop(cognito_sampler, "HTTPSampler.path", "${COGNITO_TOKEN_URL}")
        self._add_string_prop(cognito_sampler, "HTTPSampler.method", "POST")
        self._add_bool_prop(cognito_sampler, "HTTPSampler.follow_redirects", True)
        self._add_bool_prop(cognito_sampler, "HTTPSampler.auto_redirects", False)
        self._add_bool_prop(cognito_sampler, "HTTPSampler.use_keepalive", True)
        self._add_bool_prop(cognito_sampler, "HTTPSampler.DO_MULTIPART_POST", False)

        # Body Parameters for Cognito Token Endpoint
        cognito_args = ET.SubElement(cognito_sampler, "elementProp", {
            "name": "HTTPsampler.Arguments",
            "elementType": "Arguments",
            "guiclass": "HTTPArgumentsPanel",
            "testclass": "Arguments",
            "testname": "Cognito Parameters",
            "enabled": "true"
        })
        c_args_coll = ET.SubElement(cognito_args, "collectionProp", {"name": "Arguments.arguments"})
        c_params = [
            ("grant_type", "client_credentials"),
            ("client_id", "${COGNITO_CLIENT_ID}"),
            ("client_secret", "${COGNITO_CLIENT_SECRET}"),
            ("scope", "${COGNITO_SCOPE}"),
        ]
        for p_name, p_val in c_params:
            arg_el = ET.SubElement(c_args_coll, "elementProp", {"name": p_name, "elementType": "HTTPArgument"})
            self._add_bool_prop(arg_el, "HTTPArgument.always_encode", True)
            self._add_string_prop(arg_el, "Argument.name", p_name)
            self._add_string_prop(arg_el, "Argument.value", p_val)
            self._add_string_prop(arg_el, "Argument.metadata", "=")
            self._add_bool_prop(arg_el, "HTTPArgument.use_equals", True)

        cognito_hash = ET.SubElement(once_hash, "hashTree")

        # 5.2 Header Manager specific for Cognito Request (Override Content-Type)
        c_header_mgr = ET.SubElement(cognito_hash, "HeaderManager", {
            "guiclass": "HeaderPanel",
            "testclass": "HeaderManager",
            "testname": "Cognito Auth Header",
            "enabled": "true"
        })
        c_h_coll = ET.SubElement(c_header_mgr, "collectionProp", {"name": "HeaderManager.headers"})
        c_h = ET.SubElement(c_h_coll, "elementProp", {"name": "", "elementType": "Header"})
        self._add_string_prop(c_h, "Header.name", "Content-Type")
        self._add_string_prop(c_h, "Header.value", "application/x-www-form-urlencoded")
        ET.SubElement(cognito_hash, "hashTree")

        # 5.3 JSON Extractor (Modern standard: $.access_token)
        json_ext = ET.SubElement(cognito_hash, "JSONPostProcessor", {
            "guiclass": "JSONPostProcessorGui",
            "testclass": "JSONPostProcessor",
            "testname": "JSON Extractor - access_token",
            "enabled": "true"
        })
        self._add_string_prop(json_ext, "JSONPostProcessor.referenceNames", "cognito_access_token")
        self._add_string_prop(json_ext, "JSONPostProcessor.jsonPathExprs", "$.access_token")
        self._add_string_prop(json_ext, "JSONPostProcessor.match_numbers", "1")
        self._add_string_prop(json_ext, "JSONPostProcessor.defaultValues", "COGNITO_TOKEN_NOT_FOUND")
        ET.SubElement(cognito_hash, "hashTree")

        # 5.4 Regular Expression Extractor (Backup / Explicit user requirement)
        regex_ext = ET.SubElement(cognito_hash, "RegexExtractor", {
            "guiclass": "RegexExtractorGui",
            "testclass": "RegexExtractor",
            "testname": "RegEx Extractor - access_token",
            "enabled": "true"
        })
        self._add_string_prop(regex_ext, "RegexExtractor.useHeaders", "false")
        self._add_string_prop(regex_ext, "RegexExtractor.refname", "cognito_access_token_regex")
        self._add_string_prop(regex_ext, "RegexExtractor.regex", '"access_token"\\s*:\\s*"([^"]+)"')
        self._add_string_prop(regex_ext, "RegexExtractor.template", "$1$")
        self._add_string_prop(regex_ext, "RegexExtractor.default", "COGNITO_TOKEN_NOT_FOUND")
        self._add_string_prop(regex_ext, "RegexExtractor.match_number", "1")
        ET.SubElement(cognito_hash, "hashTree")

        # 6. API Gateway Endpoints from OpenAPI paths
        paths = self.spec.get("paths", {})
        sampler_index = 1

        for raw_path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method_name in ("get", "post", "put", "delete", "patch", "options", "head"):
                if method_name not in path_item:
                    continue
                operation = path_item[method_name]
                if not isinstance(operation, dict):
                    continue

                op_id = operation.get("operationId", f"{method_name.upper()}_{raw_path.replace('/', '_')}")
                summary = operation.get("summary", f"{method_name.upper()} {raw_path}")
                sampler_name = f"{sampler_index:02d}_{method_name.upper()}_{raw_path}"
                sampler_index += 1

                # Resolve Path Parameters and Query Parameters
                parameters = operation.get("parameters", [])
                # Also include path-level parameters if any
                if "parameters" in path_item and isinstance(path_item["parameters"], list):
                    parameters = path_item["parameters"] + parameters

                actual_path = raw_path
                query_args = []

                for param in parameters:
                    if "$ref" in param:
                        param = self.mock_gen.resolve_ref(param["$ref"])
                    p_name = param.get("name")
                    p_in = param.get("in")
                    p_schema = param.get("schema", {})
                    p_val = self.mock_gen.generate_value(p_schema)

                    if p_in == "path":
                        actual_path = actual_path.replace(f"{{{p_name}}}", str(p_val))
                    elif p_in == "query":
                        query_args.append((p_name, str(p_val)))

                # Resolve Request Body (JSON)
                has_body = False
                body_json_str = ""
                request_body = operation.get("requestBody", {})
                if "$ref" in request_body:
                    request_body = self.mock_gen.resolve_ref(request_body["$ref"])

                if request_body and "content" in request_body:
                    content_dict = request_body["content"]
                    if "application/json" in content_dict:
                        json_schema = content_dict["application/json"].get("schema", {})
                        mock_body_data = self.mock_gen.generate_value(json_schema)
                        body_json_str = json.dumps(mock_body_data, indent=2, ensure_ascii=False)
                        has_body = True

                # Create HTTP Sampler for this API operation
                api_sampler = ET.SubElement(tg_hash, "HTTPSamplerProxy", {
                    "guiclass": "HttpTestSampleGui",
                    "testclass": "HTTPSamplerProxy",
                    "testname": sampler_name,
                    "enabled": "true"
                })
                self._add_string_prop(api_sampler, "TestPlan.comments", summary)
                self._add_string_prop(api_sampler, "HTTPSampler.domain", "${TARGET_HOST}")
                self._add_string_prop(api_sampler, "HTTPSampler.port", "${TARGET_PORT}")
                self._add_string_prop(api_sampler, "HTTPSampler.protocol", "${TARGET_PROTOCOL}")
                self._add_string_prop(api_sampler, "HTTPSampler.contentEncoding", "UTF-8")
                self._add_string_prop(api_sampler, "HTTPSampler.path", actual_path)
                self._add_string_prop(api_sampler, "HTTPSampler.method", method_name.upper())
                self._add_bool_prop(api_sampler, "HTTPSampler.follow_redirects", True)
                self._add_bool_prop(api_sampler, "HTTPSampler.auto_redirects", False)
                self._add_bool_prop(api_sampler, "HTTPSampler.use_keepalive", True)
                self._add_bool_prop(api_sampler, "HTTPSampler.DO_MULTIPART_POST", False)

                args_elem = ET.SubElement(api_sampler, "elementProp", {
                    "name": "HTTPsampler.Arguments",
                    "elementType": "Arguments",
                    "guiclass": "HTTPArgumentsPanel",
                    "testclass": "Arguments",
                    "testname": "User Defined Variables",
                    "enabled": "true"
                })
                args_coll = ET.SubElement(args_elem, "collectionProp", {"name": "Arguments.arguments"})

                if has_body:
                    self._add_bool_prop(api_sampler, "HTTPSampler.postBodyRaw", True)
                    body_arg = ET.SubElement(args_coll, "elementProp", {"name": "", "elementType": "HTTPArgument"})
                    self._add_bool_prop(body_arg, "HTTPArgument.always_encode", False)
                    self._add_string_prop(body_arg, "Argument.value", body_json_str)
                    self._add_string_prop(body_arg, "Argument.metadata", "=")
                else:
                    self._add_bool_prop(api_sampler, "HTTPSampler.postBodyRaw", False)
                    for q_name, q_val in query_args:
                        q_arg = ET.SubElement(args_coll, "elementProp", {"name": q_name, "elementType": "HTTPArgument"})
                        self._add_bool_prop(q_arg, "HTTPArgument.always_encode", True)
                        self._add_string_prop(q_arg, "Argument.name", q_name)
                        self._add_string_prop(q_arg, "Argument.value", q_val)
                        self._add_string_prop(q_arg, "Argument.metadata", "=")
                        self._add_bool_prop(q_arg, "HTTPArgument.use_equals", True)

                ET.SubElement(tg_hash, "hashTree")

        # 7. Listeners: View Results Tree & Summary Report (GUI viewable & writing to JTL/Log)
        # 7.1 View Results Tree
        vrt_listener = ET.SubElement(test_plan_hash, "ResultCollector", {
            "guiclass": "ViewResultsFullVisualizer",
            "testclass": "ResultCollector",
            "testname": "View Results Tree",
            "enabled": "true"
        })
        self._add_bool_prop(vrt_listener, "ResultCollector.error_logging", False)
        vrt_obj = ET.SubElement(vrt_listener, "objProp")
        vrt_val = ET.SubElement(vrt_obj, "value", {"class": "SampleSaveConfiguration"})
        for prop_name, prop_state in [
            ("time", True), ("latency", True), ("timestamp", True), ("success", True),
            ("label", True), ("code", True), ("message", True), ("threadName", True),
            ("dataType", True), ("encoding", False), ("assertions", True), ("subresults", True),
            ("responseData", True), ("samplerData", True), ("xml", False), ("fieldNames", True),
            ("responseHeaders", True), ("requestHeaders", True), ("responseDataOnError", True),
            ("saveAssertionResultsFailureMessage", True), ("assertionsResultsToSave", 0),
            ("bytes", True), ("sentBytes", True), ("url", True), ("threadCounts", True),
            ("idleTime", True), ("connectTime", True)
        ]:
            c_tag = ET.SubElement(vrt_val, prop_name)
            c_tag.text = "true" if prop_state is True else ("false" if prop_state is False else str(prop_state))

        self._add_string_prop(vrt_listener, "filename", "${JTL_PATH}")
        ET.SubElement(test_plan_hash, "hashTree")

        # 7.2 Summary Report
        sum_listener = ET.SubElement(test_plan_hash, "ResultCollector", {
            "guiclass": "SummaryReport",
            "testclass": "ResultCollector",
            "testname": "Summary Report",
            "enabled": "true"
        })
        self._add_bool_prop(sum_listener, "ResultCollector.error_logging", False)
        sum_obj = ET.SubElement(sum_listener, "objProp")
        sum_val = ET.SubElement(sum_obj, "value", {"class": "SampleSaveConfiguration"})
        for prop_name, prop_state in [
            ("time", True), ("latency", True), ("timestamp", True), ("success", True),
            ("label", True), ("code", True), ("message", True), ("threadName", True),
            ("dataType", True), ("encoding", False), ("assertions", True), ("subresults", True),
            ("responseData", False), ("samplerData", False), ("xml", False), ("fieldNames", True),
            ("responseHeaders", False), ("requestHeaders", False), ("responseDataOnError", True),
            ("saveAssertionResultsFailureMessage", True), ("assertionsResultsToSave", 0),
            ("bytes", True), ("sentBytes", True), ("url", True), ("threadCounts", True),
            ("idleTime", True), ("connectTime", True)
        ]:
            c_tag = ET.SubElement(sum_val, prop_name)
            c_tag.text = "true" if prop_state is True else ("false" if prop_state is False else str(prop_state))

        self._add_string_prop(sum_listener, "filename", "${JTL_PATH}")
        ET.SubElement(test_plan_hash, "hashTree")

        return root


def prettify_xml(elem):
    """Returns a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    # Clean up empty lines from minidom
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate JMeter 5.6.3 JMX Scenario from OpenAPI Specification")
    parser.add_argument("-i", "--input", required=True, help="Input OpenAPI specification file (YAML or JSON)")
    parser.add_argument("-o", "--output", default="scenario.jmx", help="Output JMeter test plan file (.jmx)")
    parser.add_argument("-h_host", "--host", default="localhost", help="Target API Host (default: localhost)")
    parser.add_argument("-p", "--port", default="8080", help="Target API Port (default: 8080)")
    parser.add_argument("--protocol", default="http", help="Protocol: http or https (default: http)")
    parser.add_argument("-k", "--api-key", default="XXXXXXXXXXXX", help="Fixed X-API-KEY value (default: XXXXXXXXXXXX)")
    parser.add_argument("--cognito-token-url", default="https://auth.example.com/oauth2/token", help="Cognito OAuth2 Token Endpoint URL")
    parser.add_argument("--cognito-client-id", default="your_cognito_client_id", help="Cognito Client ID")
    parser.add_argument("--cognito-client-secret", default="your_cognito_client_secret", help="Cognito Client Secret")
    parser.add_argument("--cognito-scope", default="api/read api/write", help="OAuth2 Scope")
    parser.add_argument("--jtl", default="results.jtl", help="JTL Output path (default: results.jtl)")
    parser.add_argument("--log", default="jmeter.log", help="Log output path (default: jmeter.log)")

    args = parser.parse_args()

    print(f"[INFO] Reading OpenAPI specification: {args.input}")
    spec = load_openapi_spec(args.input)
    print(f"[INFO] OpenAPI parsed successfully. Title: {spec.get('info', {}).get('title', 'N/A')}")

    builder = JMeterScenarioBuilder(
        spec=spec,
        target_host=args.host,
        target_port=args.port,
        target_protocol=args.protocol,
        api_key=args.api_key,
        cognito_token_url=args.cognito_token_url,
        cognito_client_id=args.cognito_client_id,
        cognito_client_secret=args.cognito_client_secret,
        cognito_scope=args.cognito_scope,
        jtl_path=args.jtl,
        log_path=args.log
    )

    print(f"[INFO] Constructing JMeter 5.6.3 Test Plan...")
    root_xml = builder.build_jmx()
    xml_str = prettify_xml(root_xml)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"[SUCCESS] JMeter 5.6.3 scenario successfully generated: {args.output}")
    print(f"          - Thread Group: 1 thread, 1 loop, 1s ramp-up (single request check)")
    print(f"          - Target Endpoint: {args.protocol}://{args.host}:{args.port}")
    print(f"          - Fixed Header: X-API-KEY: {args.api_key}")
    print(f"          - Authentication: Cognito OAuth2 Token -> Bearer ${{cognito_access_token}}")
    print(f"          - Reporting: {args.jtl} & {args.log} (GUI Viewable)")


if __name__ == "__main__":
    main()
