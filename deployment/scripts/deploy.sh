#!/bin/bash
set -e

# RAG Anything with AWS Bedrock Deployment Script
# This script deploys the infrastructure and application using CloudFormation

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="raganything-bedrock"
TEMPLATE_FILE="deployment/cloudformation/bedrock-rag-infrastructure.yaml"
REGION="us-east-1"
ENVIRONMENT="development"

# Default parameters
INSTANCE_TYPE="t3.large"
VOLUME_SIZE="50"
ALLOWED_SSH_CIDR="0.0.0.0/0"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Help function
show_help() {
    cat << EOF
RAG Anything with AWS Bedrock Deployment Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -s, --stack-name NAME   CloudFormation stack name (default: $STACK_NAME)
    -r, --region REGION     AWS region (default: $REGION)
    -e, --environment ENV   Environment (development|staging|production) (default: $ENVIRONMENT)
    -k, --key-pair NAME     EC2 Key Pair name (required)
    -t, --instance-type TYPE EC2 instance type (default: $INSTANCE_TYPE)
    -v, --volume-size SIZE  EBS volume size in GB (default: $VOLUME_SIZE)
    -c, --ssh-cidr CIDR     CIDR block for SSH access (default: $ALLOWED_SSH_CIDR)
    --validate-only         Only validate the template, don't deploy
    --delete                Delete the stack instead of creating/updating

Examples:
    $0 --key-pair my-key-pair
    $0 --key-pair my-key-pair --instance-type m5.large --environment production
    $0 --delete --stack-name raganything-bedrock
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -k|--key-pair)
            KEY_PAIR_NAME="$2"
            shift 2
            ;;
        -t|--instance-type)
            INSTANCE_TYPE="$2"
            shift 2
            ;;
        -v|--volume-size)
            VOLUME_SIZE="$2"
            shift 2
            ;;
        -c|--ssh-cidr)
            ALLOWED_SSH_CIDR="$2"
            shift 2
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --delete)
            DELETE_STACK=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed. Please install it first."
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    error "Template file not found: $TEMPLATE_FILE"
fi

# Validate AWS credentials
log "Validating AWS credentials..."
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    error "AWS credentials are not configured or invalid"
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
log "Using AWS Account: $ACCOUNT_ID"
log "Using AWS Region: $REGION"

# Check if Bedrock is available in the region
log "Checking Bedrock availability in region $REGION..."
if ! aws bedrock list-foundation-models --region "$REGION" &> /dev/null; then
    error "Bedrock is not available in region $REGION or you don't have access"
fi

# Function to delete stack
delete_stack() {
    log "Deleting CloudFormation stack: $STACK_NAME"
    
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        warn "Stack $STACK_NAME does not exist"
        return 0
    fi
    
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    log "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    log "✅ Stack deleted successfully"
}

# Function to validate template
validate_template() {
    log "Validating CloudFormation template..."
    
    aws cloudformation validate-template \
        --template-body file://"$TEMPLATE_FILE" \
        --region "$REGION" > /dev/null
    
    log "✅ Template validation successful"
}

# Function to deploy stack
deploy_stack() {
    # Check if key pair name is provided
    if [ -z "$KEY_PAIR_NAME" ]; then
        error "Key pair name is required. Use --key-pair option."
    fi
    
    # Validate key pair exists
    if ! aws ec2 describe-key-pairs --key-names "$KEY_PAIR_NAME" --region "$REGION" &> /dev/null; then
        error "Key pair '$KEY_PAIR_NAME' does not exist in region $REGION"
    fi
    
    # Prepare parameters
    PARAMETERS="ParameterKey=InstanceType,ParameterValue=$INSTANCE_TYPE"
    PARAMETERS="$PARAMETERS ParameterKey=KeyPairName,ParameterValue=$KEY_PAIR_NAME"
    PARAMETERS="$PARAMETERS ParameterKey=AllowedSSHCIDR,ParameterValue=$ALLOWED_SSH_CIDR"
    PARAMETERS="$PARAMETERS ParameterKey=VolumeSize,ParameterValue=$VOLUME_SIZE"
    PARAMETERS="$PARAMETERS ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        log "Updating existing CloudFormation stack: $STACK_NAME"
        
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://"$TEMPLATE_FILE" \
            --parameters $PARAMETERS \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        log "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        log "✅ Stack updated successfully"
    else
        log "Creating new CloudFormation stack: $STACK_NAME"
        
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://"$TEMPLATE_FILE" \
            --parameters $PARAMETERS \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" \
            --enable-termination-protection
        
        log "Waiting for stack creation to complete..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        log "✅ Stack created successfully"
    fi
}

# Function to get stack outputs
get_stack_outputs() {
    log "Getting stack outputs..."
    
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table)
    
    echo "$OUTPUTS"
    
    # Get specific outputs
    INSTANCE_ID=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
        --output text)
    
    PUBLIC_IP=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`InstancePublicIP`].OutputValue' \
        --output text)
    
    SSH_COMMAND=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`SSHCommand`].OutputValue' \
        --output text)
    
    echo
    log "📋 Deployment Summary:"
    echo "  Instance ID: $INSTANCE_ID"
    echo "  Public IP: $PUBLIC_IP"
    echo "  SSH Command: $SSH_COMMAND"
    echo
    log "📝 Next Steps:"
    echo "  1. Wait for the instance to fully initialize (5-10 minutes)"
    echo "  2. SSH to the instance: $SSH_COMMAND"
    echo "  3. Check installation status: sudo tail -f /var/log/cloud-init-output.log"
    echo "  4. Test the application: sudo -u raganything /opt/raganything/scripts/test_bedrock.py"
    echo "  5. Start the service: /opt/raganything/scripts/start.sh"
}

# Main execution
log "🚀 Starting RAG Anything with AWS Bedrock deployment..."
log "Stack Name: $STACK_NAME"
log "Region: $REGION"
log "Environment: $ENVIRONMENT"

# Validate template first
validate_template

# Handle different operations
if [ "$VALIDATE_ONLY" = true ]; then
    log "✅ Template validation completed successfully"
    exit 0
elif [ "$DELETE_STACK" = true ]; then
    delete_stack
    exit 0
else
    deploy_stack
    get_stack_outputs
fi

log "🎉 Deployment completed successfully!"