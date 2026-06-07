targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------
@minLength(1)
@maxLength(64)
@description('Name of the environment (used to generate resource names)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Name of the model to deploy')
param modelName string = 'gpt-4.1-mini'

@description('Version of the model to deploy')
param modelVersion string = '2025-04-14'

@description('Model format (OpenAI for GPT models)')
param modelFormat string = 'OpenAI'

@description('SKU name for the model deployment')
param modelSkuName string = 'GlobalStandard'

@description('Capacity (tokens-per-minute in thousands) for the model')
param modelCapacity int = 10

@description('Optional: deploy a second model for comparison lab')
param deploySecondModel bool = false

@description('Second model name (for comparison lab)')
param secondModelName string = 'gpt-4.1'

@description('Second model version')
param secondModelVersion string = '2025-04-14'

@description('Second model capacity')
param secondModelCapacity int = 10

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Type of the principal: User or ServicePrincipal. Use ServicePrincipal for unattended/Skillable deployments.')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalType string = 'User'

@description('Enable hosted agent infrastructure (ACR + capability host) for Lab 6')
param enableHostedAgents bool = false

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  'lab': 'get-started-foundry-models'
}

// ---------------------------------------------------------------------------
// Resource Group
// ---------------------------------------------------------------------------
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// ---------------------------------------------------------------------------
// Monitoring (Log Analytics + Application Insights)
// ---------------------------------------------------------------------------
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

// ---------------------------------------------------------------------------
// Azure AI Services (Foundry Account) + Project + Model Deployment
// ---------------------------------------------------------------------------
module aiServices './modules/ai-services.bicep' = {
  name: 'ai-services'
  scope: rg
  params: {
    location: location
    tags: tags
    aiServicesName: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    projectName: '${environmentName}-project'
    applicationInsightsId: monitoring.outputs.applicationInsightsId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    modelName: modelName
    modelVersion: modelVersion
    modelFormat: modelFormat
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
    deploySecondModel: deploySecondModel
    secondModelName: secondModelName
    secondModelVersion: secondModelVersion
    secondModelCapacity: secondModelCapacity
    enableHostedAgents: enableHostedAgents
  }
}

// ---------------------------------------------------------------------------
// Role Assignments (for the lab user / service principal)
// ---------------------------------------------------------------------------
module roleAssignments './modules/role-assignments.bicep' = if (!empty(principalId)) {
  name: 'role-assignments'
  scope: rg
  params: {
    principalId: principalId
    principalType: principalType
    aiServicesName: aiServices.outputs.aiServicesName
    acrName: enableHostedAgents ? aiServices.outputs.acrName : ''
  }
}

// ---------------------------------------------------------------------------
// Outputs (consumed by azd env get-values)
// ---------------------------------------------------------------------------
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_AI_SERVICES_NAME string = aiServices.outputs.aiServicesName
output AZURE_AI_PROJECT_NAME string = aiServices.outputs.projectName
output AZURE_AI_PROJECT_ID string = aiServices.outputs.projectId
output AZURE_AI_PROJECT_ENDPOINT string = aiServices.outputs.projectEndpoint
output AZURE_APPLICATION_INSIGHTS_NAME string = monitoring.outputs.applicationInsightsName
output MODEL_DEPLOYMENT_NAME string = modelName
output MODEL_DEPLOYMENT_NAME_2 string = deploySecondModel ? secondModelName : ''
output AZURE_CONTAINER_REGISTRY_NAME string = enableHostedAgents ? aiServices.outputs.acrName : ''
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = enableHostedAgents ? aiServices.outputs.acrLoginServer : ''
