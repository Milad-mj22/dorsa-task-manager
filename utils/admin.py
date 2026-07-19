from django.contrib import admin

# Register your models here.
from utils.models import ProjectTicket, Ticket, TicketCategory

# Register your models here.
admin.site.register(TicketCategory)
admin.site.register(Ticket)

admin.site.register(ProjectTicket)


