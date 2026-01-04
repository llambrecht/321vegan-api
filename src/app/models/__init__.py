from app.models.user import User, Base
from app.models.brand import Brand
from app.models.product import Product
from app.models.cosmetic import Cosmetic
from app.models.apiclient import ApiClient
from app.models.error_report import ErrorReport
from app.models.checking import Checking
from app.models.scoring import Category, Criterion, BrandCriterionScore
from app.models.product_category import ProductCategory
from app.models.interesting_product import InterestingProduct, InterestingProductType
from app.models.scan_event import ScanEvent