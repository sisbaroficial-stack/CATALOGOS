from .models import ConfiguracionCatalogo


def catalogo_config(request):
    return {'catalogo_config': ConfiguracionCatalogo.get_solo()}
