# Advanced Configuration Management

This directory contains the advanced configuration system for the Sanskrit Processor, supporting environment-specific configurations and environment variable substitution.

## Configuration Structure

```
config/
├── config.base.yaml        # Base configuration (required)
├── config.dev.yaml         # Development environment overrides
├── config.staging.yaml     # Staging environment overrides
├── config.prod.yaml        # Production environment overrides
└── README.md              # This documentation
```

## Environment Detection

The system automatically detects the environment using the `ENVIRONMENT` environment variable:

```bash
# Development (default)
python3 cli.py input.srt output.srt

# Production
ENVIRONMENT=prod python3 cli.py input.srt output.srt

# Staging
ENVIRONMENT=staging python3 cli.py input.srt output.srt
```

## Configuration Inheritance

Environment-specific configurations inherit from and override the base configuration:

1. **Base Configuration**: `config.base.yaml` provides default values
2. **Environment Override**: `config.{env}.yaml` overrides specific values
3. **Deep Merging**: Nested objects are merged, not replaced

### Example

**config.base.yaml:**
```yaml
services:
  api:
    timeout: 10
    retries: 3
    enabled: false
```

**config.prod.yaml:**
```yaml
services:
  api:
    timeout: 5      # Override
    enabled: true   # Override
    # retries: 3 inherited from base
```

**Effective Production Config:**
```yaml
services:
  api:
    timeout: 5      # From prod override
    retries: 3      # From base
    enabled: true   # From prod override
```

## Environment Variable Substitution

Use environment variables in configuration files with the syntax `${VAR_NAME}` or `${VAR_NAME:default_value}`:

```yaml
services:
  api:
    base_url: "${API_BASE_URL:http://localhost:8080}"
    api_key: "${API_KEY}"  # Required - no default
    timeout: "${API_TIMEOUT:30}"
```

### Environment Variable Examples

```bash
# Use defaults where available
python3 cli.py input.srt output.srt

# Override with environment variables
API_BASE_URL="https://api.prod.example.com" \
API_KEY="prod_key_123" \
API_TIMEOUT="5" \
ENVIRONMENT=prod \
python3 cli.py input.srt output.srt
```

## Migration from Legacy Configuration

If you have an existing `config.yaml` file, use the migration tool:

```bash
# Migrate existing config to new structure
python3 tools/migrate_config.py config.yaml config/

# Your original config.yaml will be backed up automatically
```

## Configuration Validation

Validate your configuration and see the effective merged result:

```bash
# Validate current environment configuration
python3 cli.py --validate-config

# Validate specific environment
ENVIRONMENT=prod python3 cli.py --validate-config
```

## Backward Compatibility

The system maintains full backward compatibility:

- **Legacy Support**: Existing `config.yaml` files continue to work
- **Automatic Fallback**: If advanced config fails, falls back to legacy loading
- **Optional Migration**: You can upgrade when ready, no forced migration

## Security Best Practices

### Sensitive Values
- **Never commit**: API keys, passwords, or tokens to version control
- **Use Environment Variables**: Store sensitive values as environment variables
- **Production Deployment**: Use secure environment variable management

### File Permissions
```bash
# Restrict access to configuration files
chmod 600 config/*.yaml

# Or use directory permissions
chmod 700 config/
```

### Example Production Setup
```bash
# Set environment variables securely
export API_KEY="$(cat /secure/api-key.txt)"
export DB_PASSWORD="$(vault kv get -field=password secret/db)"
export ENVIRONMENT="prod"

# Run with restricted permissions
umask 077
python3 cli.py input.srt output.srt
```

## Troubleshooting

### Common Issues

**Error: "Required environment variable not set"**
- Set the required environment variable or add a default value in config
- Check variable names for typos

**Error: "No base configuration found"**
- Ensure `config/config.base.yaml` exists
- Or use migration tool to create advanced configuration structure

**Error: "Invalid YAML"**
- Validate YAML syntax with online validator
- Check indentation (use spaces, not tabs)
- Ensure proper quoting of special characters

### Debug Configuration Loading
```bash
# Enable verbose logging
python3 cli.py --validate-config --verbose

# Check effective configuration
ENVIRONMENT=dev python3 cli.py --validate-config
```

## Configuration Examples

### Development Environment
Focus on debugging and testing:
```yaml
# config.dev.yaml
processing:
  fuzzy_matching:
    log_matches: true
    threshold: 0.7

logging:
  level: "DEBUG"

environment:
  debug: true

plugins:
  enabled: true
  enabled_plugins:
    - performance_monitor
    - debug_helper
```

### Production Environment
Focus on performance and security:
```yaml
# config.prod.yaml
processing:
  fuzzy_matching:
    log_matches: false
    threshold: 0.85

logging:
  level: "WARNING"
  json_output: true

environment:
  debug: false

security:
  strict_validation: true

plugins:
  enabled: false  # Minimal dependencies in production
```

For more information, see the main project documentation in `CLAUDE.md`.