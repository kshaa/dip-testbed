package diptestbed.domain

import diptestbed.domain.DomainTimeZone.getBaseZoneFromString

case class DomainTimeZoneId(value: String) extends AnyVal {
  def zone: DomainTimeZone = DomainTimeZone.fromString(this.value).toOption.get
}

object DomainTimeZoneId {
  def fromString(timezoneId: String): Either[Throwable, DomainTimeZoneId] =
    getBaseZoneFromString(timezoneId).map(id => DomainTimeZoneId(id.getId))
}
