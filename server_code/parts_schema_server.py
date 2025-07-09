from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List, Union
from datetime import date, datetime
from pymongo import MongoClient


# ---------- Vendor Models ----------

class Address(BaseModel):
  line1: str
  line2: str
  city: str
  state: str
  postal_code: str
  country: str

class Contact(BaseModel):
  name: str
  email: str
  phone: str

class Vendor(BaseModel):
  _id: str
  company_name: str
  address: Address
  contact: Contact
  categories: List[str]
  status: str


# ---------- Part Models ----------

class Cost(BaseModel):
  cost_date: Optional[date] = None
  cost_nz: float = 0.0

  @validator('cost_date', pre=True, always=True)
  def parse_cost_date(cls, v):
    if not v:
      return None
    if isinstance(v, str):
      try:
        return datetime.strptime(v, "%Y-%m-%d").date()
      except ValueError:
        return None
    return v

  @validator('cost_nz', pre=True, always=True)
  def convert_cost_nz(cls, v):
    if v in [None, "", "-", float("nan")]:
      return 0.0
    if isinstance(v, dict) and '$numberDouble' in v:
      val = v['$numberDouble']
      if val in ['Infinity', '-Infinity', 'NaN']:
        return 0.0
      return float(val)
    return float(v)

class VendorPartNumber(BaseModel):
  vendor_id: str
  vendor_part_no: str
  vendor_currency: str
  cost_date: Optional[date] = None
  cost_NZ: float = Field(0.0, alias='cost_$NZ')
  vendor_price: float = 0.0

  @validator('cost_date', pre=True, always=True)
  def parse_cost_date(cls, v):
    if not v:
      return None
    if isinstance(v, str):
      try:
        return datetime.strptime(v, "%Y-%m-%d").date()
      except ValueError:
        return None
    return v

  @validator('cost_NZ', 'vendor_price', pre=True, always=True)
  def convert_prices(cls, v):
    if v in [None, "", "-", float("nan")]:
      return 0.0
    if isinstance(v, dict) and '$numberDouble' in v:
      return float(v['$numberDouble'])
    return float(v)

class Part(BaseModel):
  _id: str
  default_vendor: str
  description: str
  group_code: str
  latest_cost: Cost
  material_spec: str
  process: str
  revision: str
  root_serial: str
  status: str
  type: str
  unit: str
  variant: str
  vendor_part_numbers: List[VendorPartNumber]


# ---------- MongoDB Integration Helpers ----------

import os

from dotenv import load_dotenv
load_dotenv()
uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

client = MongoClient(uri)
db = client.manufacturing  # Replace with your actual DB name


def validate_and_save_part(data: dict) -> dict:
  """Validate part and insert into MongoDB."""
  try:
    part = Part(**data)
    db.parts.replace_one({'_id': part._id}, part.dict(by_alias=True), upsert=True)
    return part.dict()
  except ValidationError as e:
    print(f"Validation error: {e.json()}")
    raise


def validate_all_parts():
  """Run validation across all records in the parts collection."""
  invalid = []
  for doc in db.parts.find():
    try:
      Part(**doc)
    except ValidationError as e:
      invalid.append((doc.get("_id"), e))
  return invalid


