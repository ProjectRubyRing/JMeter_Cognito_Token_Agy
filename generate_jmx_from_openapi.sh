#!/bin/bash
# ==============================================================================
# Script Name: generate_jmx_from_openapi.sh
# Description: Generates JMeter 5.6.3 JMX test plan from OpenAPI Specification (YAML/JSON)
# Target OS  : Red Hat Enterprise Linux (RHEL) 9.8 / CentOS Stream 9 / Rocky Linux 9
# ==============================================================================

set -euo pipefail

# Default Configuration Parameters
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_ENGINE="${SCRIPT_DIR}/openapi_to_jmx.py"

INPUT_FILE=""
OUTPUT_FILE="scenario.jmx"
TARGET_HOST="localhost"
TARGET_PORT="8080"
TARGET_PROTOCOL="http"
API_KEY="XXXXXXXXXXXX"
COGNITO_TOKEN_URL="https://auth.example.com/oauth2/token"
COGNITO_CLIENT_ID="your_cognito_client_id"
COGNITO_CLIENT_SECRET="your_cognito_client_secret"
COGNITO_SCOPE="api/read api/write"
JTL_PATH="results.jtl"
LOG_PATH="jmeter.log"

# Color Codes for Terminal Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function: Display Usage
usage() {
    cat << EOF
Usage: $(basename "$0") -i <openapi_file> [OPTIONS]

Required:
  -i, --input <file>           OpenAPI specification file path (.yaml, .yml, or .json)

Options:
  -o, --output <file>          Output JMeter JMX scenario path (default: ${OUTPUT_FILE})
  -h, --host <hostname>        Target API Server Host (default: ${TARGET_HOST})
  -p, --port <port>            Target API Server Port (default: ${TARGET_PORT})
  --protocol <protocol>        Protocol: http or https (default: ${TARGET_PROTOCOL})
  -k, --api-key <key>          Fixed X-API-KEY header value (default: ${API_KEY})
  --token-url <url>            Cognito OAuth2 Token Endpoint URL (default: ${COGNITO_TOKEN_URL})
  --client-id <id>             Cognito App Client ID (default: ${COGNITO_CLIENT_ID})
  --client-secret <secret>     Cognito App Client Secret (default: ${COGNITO_CLIENT_SECRET})
  --scope <scope>              OAuth2 Scope (default: ${COGNITO_SCOPE})
  --jtl <path>                 JTL result file output path (default: ${JTL_PATH})
  --log <path>                 Log file output path (default: ${LOG_PATH})
  --help                       Display this help message

Example (RHEL 9.8):
  ./$(basename "$0") -i api_spec.yaml -o my_test_plan.jmx -h localhost -p 8080 -k XXXXXXXXXXXX
EOF
    exit "${1:-1}"
}

# Parse Command-line Arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--input)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--host)
            TARGET_HOST="$2"
            shift 2
            ;;
        -p|--port)
            TARGET_PORT="$2"
            shift 2
            ;;
        --protocol)
            TARGET_PROTOCOL="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        --token-url)
            COGNITO_TOKEN_URL="$2"
            shift 2
            ;;
        --client-id)
            COGNITO_CLIENT_ID="$2"
            shift 2
            ;;
        --client-secret)
            COGNITO_CLIENT_SECRET="$2"
            shift 2
            ;;
        --scope)
            COGNITO_SCOPE="$2"
            shift 2
            ;;
        --jtl)
            JTL_PATH="$2"
            shift 2
            ;;
        --log)
            LOG_PATH="$2"
            shift 2
            ;;
        --help)
            usage 0
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Validate Input File
if [[ -z "${INPUT_FILE}" ]]; then
    echo -e "${RED}[ERROR] Input OpenAPI specification file (-i / --input) is required.${NC}"
    usage
fi

if [[ ! -f "${INPUT_FILE}" ]]; then
    echo -e "${RED}[ERROR] Specified input file does not exist: ${INPUT_FILE}${NC}"
    exit 1
fi

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE} OpenAPI to JMeter 5.6.3 Scenario Generator (RHEL 9.8)${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Input File        : ${YELLOW}${INPUT_FILE}${NC}"
echo -e "Output JMX File   : ${YELLOW}${OUTPUT_FILE}${NC}"
echo -e "Target Endpoint   : ${YELLOW}${TARGET_PROTOCOL}://${TARGET_HOST}:${TARGET_PORT}${NC}"
echo -e "Fixed X-API-KEY   : ${YELLOW}${API_KEY}${NC}"
echo -e "Cognito Token URL : ${YELLOW}${COGNITO_TOKEN_URL}${NC}"
echo -e "Results (JTL/Log) : ${YELLOW}${JTL_PATH} / ${LOG_PATH}${NC}"
echo -e "Thread Group      : ${YELLOW}1 thread, 1 loop, 1s ramp-up (single request check)${NC}"
echo -e "----------------------------------------------------------------------"

# Check Python Availability (Default on RHEL 9.8 is python3)
PYTHON_BIN=""
if command -v python3 &> /dev/null && python3 --version &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null && python --version &> /dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}[ERROR] python3 (or python) is required but not installed or not in PATH.${NC}"
    echo -e "Install on RHEL 9.8 with: sudo dnf install -y python3"
    exit 1
fi

# Ensure python conversion engine exists
if [[ ! -f "${PYTHON_ENGINE}" ]]; then
    echo -e "${RED}[ERROR] Conversion engine not found: ${PYTHON_ENGINE}${NC}"
    exit 1
fi

# Check YAML parsing support if input is YAML
EXT="${INPUT_FILE##*.}"
if [[ "$EXT" == "yaml" || "$EXT" == "yml" ]]; then
    if ! "$PYTHON_BIN" -c "import ruamel.yaml" &> /dev/null && ! "$PYTHON_BIN" -c "import yaml" &> /dev/null; then
        echo -e "${YELLOW}[WARNING] Neither 'ruamel.yaml' nor 'PyYAML' was detected in ${PYTHON_BIN}.${NC}"
        echo -e "Attempting to install PyYAML via pip or dnf if needed: sudo dnf install -y python3-pyyaml"
    fi
fi

# Execute Python Generator
echo -e "[1/3] Generating JMeter 5.6.3 test plan XML..."
"$PYTHON_BIN" "${PYTHON_ENGINE}" \
    --input "${INPUT_FILE}" \
    --output "${OUTPUT_FILE}" \
    --host "${TARGET_HOST}" \
    --port "${TARGET_PORT}" \
    --protocol "${TARGET_PROTOCOL}" \
    --api-key "${API_KEY}" \
    --cognito-token-url "${COGNITO_TOKEN_URL}" \
    --cognito-client-id "${COGNITO_CLIENT_ID}" \
    --cognito-client-secret "${COGNITO_CLIENT_SECRET}" \
    --cognito-scope "${COGNITO_SCOPE}" \
    --jtl "${JTL_PATH}" \
    --log "${LOG_PATH}"

# Validate Output XML
echo -e "[2/3] Validating generated XML structure for JMeter 5.6.3..."
if [[ ! -f "${OUTPUT_FILE}" ]]; then
    echo -e "${RED}[ERROR] Output JMX was not generated.${NC}"
    exit 1
fi

"$PYTHON_BIN" -c "import xml.etree.ElementTree as ET; tree = ET.parse('${OUTPUT_FILE}'); assert tree.getroot().tag == 'jmeterTestPlan'"
echo -e "${GREEN}[VALID] JMX XML structure confirmed valid!${NC}"

# Display Execution Instructions
echo -e "[3/3] Execution instructions:"
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN} Successfully generated: ${OUTPUT_FILE}${NC}"
echo -e "${GREEN}======================================================================${NC}"
cat << 'EOF'

[How to execute on RHEL 9.8 / Linux]:

1. Non-GUI (CLI) Execution (Recommended for performance/smoke test):
   jmeter -n -t scenario.jmx -l results.jtl -j jmeter.log

2. Overriding Target Host/Port at Runtime:
   jmeter -n -t scenario.jmx -JTARGET_HOST=api.example.com -JTARGET_PORT=443 -JTARGET_PROTOCOL=https

3. GUI Mode on Desktop (X11 / VNC) to inspect results visually:
   jmeter -t scenario.jmx
   -> Expand "View Results Tree" or "Summary Report" listener.
   -> Click "Browse..." and select 'results.jtl' to inspect requests and responses graphically.
EOF
