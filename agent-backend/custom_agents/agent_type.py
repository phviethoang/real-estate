from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class EvaluationFeedback(BaseModel):
    feedback: str = Field(description="Feedback to the search agent on tool usage and criteria satisfaction")
    score: Literal["pass", "needs_improvement"] = Field(description="Score based on whether 30% of listings satisfy criteria")
    reason: str = Field(description="Reason for the assigned score")


class FunctionArgs(BaseModel):
    # 1. Mở rộng Estate Type theo danh sách đầy đủ bạn cung cấp
    estate_type: List[Literal[
        "nhà mặt phố", "nhà phố", 
        "nhà riêng", "nhà trọ", "phòng trọ",
        "chung cư", "tập thể", "căn hộ",
        "biệt thự", "liền kề", "đất biệt thự",
        "đất", "đất mặt phố", "đất riêng", "đất trang trại",
        "kho xưởng", "thuê kho", 
        "văn phòng", "cửa hàng", "nhà đất khác"
    ]] = Field(..., description="Danh sách các loại bất động sản.")

    is_latest_posted: Optional[bool] = Field(description="Lấy bài đăng mới nhất")
    is_latest_created: Optional[bool] = Field(description="Lấy bài tạo mới nhất trong cơ sở dữ liệu")

    # 2. THÊM Province và BỎ Literal cứng ở District/Ward (để hỗ trợ toàn quốc)
    province: Optional[List[str]] = Field(description="Tỉnh/Thành phố")
    district: Optional[List[str]] = Field(description="Quận/Huyện/Thị xã")
    ward: Optional[List[str]] = Field(description="Phường/Xã/Thị trấn")
    # Các trường còn lại giữ nguyên
    front_face: Optional[float] = Field(description="Mặt tiền (m)")
    front_road: Optional[float] = Field(description="Đường trước nhà (m)")
    no_bathrooms: Optional[int] = Field(description="Số phòng tắm")
    no_bedrooms: Optional[int] = Field(description="Số phòng ngủ")
    no_floors: Optional[int] = Field(description="Số tầng")
    ultilization_square: Optional[float] = Field(description="Diện tích sử dụng (m²)")
    
    # Giữ logic giá/diện tích như cũ
    price: Optional[float] = Field(description="Mức giá (VNĐ)")
    price_per_square: Optional[float] = Field(description="Giá trên mét vuông")
    square: Optional[float] = Field(description="Diện tích (m²)")
    description: Optional[str] = Field(description="Mô tả bất động sản hoặc từ khóa tìm kiếm")

    class Config:
        validate_by_name = True

class Address(BaseModel):
    district: str
    full_address: str
    province: str
    ward: str

class ContactInfo(BaseModel):
    name: str
    phone: List[str]

class ExtraInfos(BaseModel):
    direction: Optional[str] = None
    front_face: Optional[float] = None
    front_road: Optional[float] = None
    no_bathrooms: Optional[int] = None
    no_bedrooms: Optional[int] = None
    no_floors: Optional[int] = None
    ultilization_square: Optional[float] = None
    yo_construction: Optional[int] = None
    legal: Optional[str] = None

class Post(BaseModel):
    address: Address
    contact_info: ContactInfo
    description: str
    estate_type: str
    extra_infos: ExtraInfos
    id: Optional[str | int] = None
    link: str
    post_date: str
    created_at: str
    post_id: str
    price: float
    price_per_square: float
    square: float
    title: str

    class Config:
        # alias_generator = lambda field_name: field_name.replace("_per_", "/")
        populate_by_name = True

class ListPosts(BaseModel):
    posts: List[Post]