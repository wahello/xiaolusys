from djangorestframework.renderers import TemplateRenderer,JSONRenderer



class PurchaseItemHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'purchases/'

    
    
class PurchaseHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'purchases/purchase_page.html'
    
    
class PurchaseStorageHtmlRenderer(TemplateRenderer):
    """
    Renderer which serializes to JSON
    """
    
    media_type = 'text/html'
    format = 'html'
    template = 'purchases/purchase_storage_page.html'
    
    