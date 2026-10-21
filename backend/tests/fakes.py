from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

from app.catalog import AdminRequired, Product, ProductNotFound, validate_photo


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.uploads = 0

    def put(self, key, photo, content_type):
        self.objects[key] = (photo, content_type)
        self.uploads += 1

    def remove(self, key):
        self.objects.pop(key, None)

    def open(self, key):
        photo, content_type = self.objects[key]
        response = BytesIO(photo)
        response.headers = {"Content-Type": content_type}
        response.stream = lambda size: iter([photo])
        response.release_conn = lambda: None
        return response


class MemoryDatabase:
    def __init__(self):
        self.roles = {}

    def ensure_user(self, telegram_id):
        return self.roles.setdefault(telegram_id, "user")

    def set_role(self, telegram_id, role):
        self.roles[telegram_id] = role


class FakeCatalog:
    def __init__(self, settings):
        self.settings = settings
        self.database = MemoryDatabase()
        self.storage = MemoryStorage()
        self.products = {}
        self.sources = {}

    def list_products(self):
        return list(self.products.values())

    def get_product(self, product_id):
        if product_id not in self.products:
            raise ProductNotFound()
        return self.products[product_id]

    def create_product(self, telegram_id, title, photo, source_key=None):
        if self.database.ensure_user(telegram_id) != "admin":
            raise AdminRequired()
        if source_key and source_key in self.sources:
            return self.sources[source_key]
        product_id = uuid4()
        image_key = f"products/{product_id}"
        self.storage.put(image_key, photo, validate_photo(photo, self.settings.max_photo_bytes))
        product = Product(
            id=product_id, title=title, image_key=image_key, created_at=datetime.now(UTC)
        )
        self.products[product_id] = product
        if source_key:
            self.sources[source_key] = product
        return product
