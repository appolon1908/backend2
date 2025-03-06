from django.contrib import admin


from .models import HeaderTitle, CaseStudy, FAQs, ContactUs, Logo, TaxPayer, Testimonial

admin.site.register(FAQs)
admin.site.register(Logo)
admin.site.register(TaxPayer)
admin.site.register(Testimonial)
admin.site.register(CaseStudy)
admin.site.register(ContactUs)
admin.site.register(HeaderTitle)