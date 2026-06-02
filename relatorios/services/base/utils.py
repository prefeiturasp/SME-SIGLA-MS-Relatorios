from django.conf import settings


def ajustar_logo_caminho(logo):
    if logo and isinstance(logo, str):
        if settings.DJANGO_ENVIRONMENT != "local":
            base_prefix = settings.MS_PATH.rstrip("/")
            if base_prefix:
                segment = f"{base_prefix}/media/"
                # apenas prefixa a primeira ocorrência de /media/
                if "/media/" in logo and segment not in logo:
                    logo = logo.replace("/media/", segment, 1)
        return logo
    return None
