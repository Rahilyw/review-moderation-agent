# Cleanup Instructions

After completing the workshop, remove the Azure resources to avoid ongoing charges.

---

## Option 1: Delete via Azure Developer CLI (Recommended)

If you provisioned using `azd provision`, the fastest cleanup is:

```bash
azd down --force --purge
```

| Flag | Purpose |
|------|---------|
| `--force` | Skip confirmation prompts |
| `--purge` | Permanently delete soft-deleted resources (AI Services, Key Vault) |

This removes the entire resource group and all resources within it.

---

## Option 2: Delete via Azure CLI

If you prefer to delete resources manually:

### Delete the resource group

```bash
az group delete --name rg-foundry-lab --yes --no-wait
```

### Purge soft-deleted AI Services (if applicable)

```bash
az cognitiveservices account purge \
  --name <your-foundry-resource-name> \
  --resource-group rg-foundry-lab \
  --location <your-region>
```

---

## Option 3: Delete via Azure Portal

1. Navigate to **[https://portal.azure.com](https://portal.azure.com)**
2. Search for **Resource groups**
3. Find `rg-foundry-lab`
4. Click **Delete resource group**
5. Type the resource group name to confirm
6. Click **Delete**

---

## Local Cleanup

Remove local files created during the workshop:

```bash
# Remove the azd project directory
rm -rf foundry-project

# Remove Python virtual environment (if created)
rm -rf .venv

# Remove the .env file (contains your endpoint)
rm .env
```

---

## Verify Cleanup

Confirm all resources are deleted:

```bash
az group show --name rg-foundry-lab 2>&1
```

Expected output: `Resource group 'rg-foundry-lab' could not be found.`

---

## Cost Note

If you do **not** delete your resources:

- **Model deployments** incur charges based on provisioned capacity (tokens per minute)
- **AI Services resource** has a base cost depending on SKU
- **Application Insights** may incur ingestion charges

Delete resources promptly after completing the lab to avoid unexpected charges.
