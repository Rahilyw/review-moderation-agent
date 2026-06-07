// ---------------------------------------------------------------------------
// Role Assignments — Skillable (supports User and ServicePrincipal)
// ---------------------------------------------------------------------------
@description('Principal ID to assign roles to (user or service principal)')
param principalId string
@description('Type of principal: User or ServicePrincipal')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalType string = 'ServicePrincipal'
@description('Name of the AI Services resource to scope role assignments')
param aiServicesName string
@description('Name of the ACR resource (empty string skips ACR role)')
param acrName string = ''
// ---------------------------------------------------------------------------
// Existing resource reference
// ---------------------------------------------------------------------------
resource aiServices 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: aiServicesName
}
// ---------------------------------------------------------------------------
// Role Definitions
// ---------------------------------------------------------------------------
// Cognitive Services OpenAI User — invoke models
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
// Cognitive Services Contributor — manage deployments
var cognitiveServicesContributorRoleId = '25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68'
// Azure AI User — required for agent create/read/write operations
var azureAIUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
// ---------------------------------------------------------------------------
// Cognitive Services OpenAI User
// ---------------------------------------------------------------------------
resource openAIUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, principalId, cognitiveServicesOpenAIUserRoleId)
  scope: aiServices
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalType: principalType
  }
}
// ---------------------------------------------------------------------------
// Cognitive Services Contributor
// ---------------------------------------------------------------------------
resource contributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, principalId, cognitiveServicesContributorRoleId)
  scope: aiServices
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesContributorRoleId)
    principalType: principalType
  }
}
// ---------------------------------------------------------------------------
// Azure AI User
// ---------------------------------------------------------------------------
resource azureAIUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServices.id, principalId, azureAIUserRoleId)
  scope: aiServices
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIUserRoleId)
    principalType: principalType
  }
}
// ---------------------------------------------------------------------------
// AcrPush — push agent container images (only when ACR is provisioned)
// ---------------------------------------------------------------------------
var acrPushRoleId = '8311e382-0749-4cb8-b61a-304f252e45ec'
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (!empty(acrName)) {
  name: acrName
}
resource acrPushRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(acrName)) {
  name: guid(acr.id, principalId, acrPushRoleId)
  scope: acr
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPushRoleId)
    principalType: principalType
  }
}