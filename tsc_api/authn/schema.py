from drf_spectacular.extensions import OpenApiAuthenticationExtension


class RegistryJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'tsc_api.authn.authentication.RegistryJWTAuthentication'
    name = 'BearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
