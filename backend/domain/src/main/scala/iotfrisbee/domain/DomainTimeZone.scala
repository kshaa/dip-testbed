package iotfrisbee.domain

import scala.util.Try
import java.time.ZoneId

case class DomainTimeZone(value: ZoneId) extends AnyVal {
  def id: DomainTimeZoneId = DomainTimeZoneId.fromString(value.getId).toOption.get
}

object DomainTimeZone {
  def getBaseZoneFromString(timezoneId: String): Either[Throwable, ZoneId] =
    Try(ZoneId.of(timezoneId)).toEither

  def fromString(timezoneId: String): Either[Throwable, DomainTimeZone] =
    getBaseZoneFromString(timezoneId).map(DomainTimeZone(_))
}
