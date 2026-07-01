from acd.models.company import Company
from acd.repositories.company_repository import CompanyRepository


class CompanyService:

    def __init__(self):

        self.repository = CompanyRepository()

    def create_company(self, name, city, website):

        empresa = Company()

        empresa.name = name

        empresa.city = city

        empresa.website = website

        self.repository.add(empresa)

    def list_companies(self):

        return self.repository.get_all()