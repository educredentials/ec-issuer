# HTTP API

[View the OpenAPI Documentation](../openapi/)

**Service Architecture**: This documentation covers two separate but integrated services:

- **ec-issuer**: Administrative service that manages templates, credential configurations, and creates offers. Handles business logic and orchestration.
- **ssi-agent**: Handles the OpenID4VCI protocol flow, including credential issuer metadata, credential offers, and credential requests. Performs the actual credential signing and delivery.

All API endpoints are defined in the OpenAPI specification.
