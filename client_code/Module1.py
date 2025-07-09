from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from datetime import date


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
  cost_date: str  # Alternatively, parse into date with validator
  cost_nz: Union[float, dict]  # Accept float or special dict (NaN, Infinity)

  @validator('cost_nz', pre=True)
  def convert_cost_nz(cls, v):
    if isinstance(v, dict) and '$numberDouble' in v:
      val = v['$numberDouble']
      if val in ['Infinity', '-Infinity', 'NaN']:
        return float('nan')  # or handle as needed
      return float(val)
    return v

class VendorPartNumber(BaseModel):
  vendor_id: str
  vendor_part_no: str
  vendor_currency: str
  cost_date: str
  cost_NZ: Union[float, dict] = Field(..., alias='cost_$NZ')
  vendor_price: Union[float, dict]

  @validator('cost_NZ', 'vendor_price', pre=True)
  def convert_prices(cls, v):
    if isinstance(v, dict) and '$numberDouble' in v:
      return float(v['$numberDouble'])
    return v

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

