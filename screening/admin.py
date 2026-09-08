from django.contrib import admin
from .models import Employee, PHCWorker, Patient, Screening, ReferralSlip

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
	list_display = ('employee_id', 'full_name', 'role', 'department', 'is_active', 'registration_status')
	search_fields = ('employee_id', 'full_name', 'phone', 'email')
	list_filter = ('is_active', 'role', 'department')

	@admin.display(boolean=True, description='Registered')
	def registration_status(self, employee):
		return employee.is_registered

admin.site.register(PHCWorker)
admin.site.register(Patient)
admin.site.register(Screening)
admin.site.register(ReferralSlip)