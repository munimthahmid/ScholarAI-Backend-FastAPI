#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="scholarai-rg"
LOCATION="eastus"
ACR_NAME="scholarai"
SUBSCRIPTION_ID="" # You'll need to fill this

echo "🚀 Setting up Azure infrastructure for ScholarAI..."

# Login to Azure (if not already logged in)
echo "📝 Logging into Azure..."
az login

# Set subscription
if [ -n "$SUBSCRIPTION_ID" ]; then
    az account set --subscription $SUBSCRIPTION_ID
fi

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Get ACR credentials
echo "🔑 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)

echo "✅ Azure setup complete!"
echo ""
echo "📋 GitHub Secrets to configure:"
echo "AZURE_CREDENTIALS: (Service Principal JSON - see instructions below)"
echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"
echo "DB_USER: your_db_username"
echo "DB_PASSWORD: your_db_password"
echo ""
echo "🔐 To create AZURE_CREDENTIALS service principal:"
SUBSCRIPTION_ID_CURRENT=$(az account show --query id --output tsv)
echo "az ad sp create-for-rbac --name 'scholarai-github' --role contributor --scopes /subscriptions/${SUBSCRIPTION_ID_CURRENT}/resourceGroups/$RESOURCE_GROUP --sdk-auth"
echo ""
echo "💰 Estimated monthly cost: $30-50 USD"
echo "🌐 Your app will be accessible at: https://$ACR_NAME-app.$LOCATION.azurecontainer.io"
