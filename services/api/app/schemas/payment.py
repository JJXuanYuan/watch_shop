from pydantic import BaseModel


class WechatPayCreateResponse(BaseModel):
    order_id: int
    order_no: str
    payment_no: str
    appId: str
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str
    prepayId: str
