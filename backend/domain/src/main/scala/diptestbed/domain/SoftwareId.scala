package diptestbed.domain

import java.util.UUID
import scala.util.Try

case class SoftwareId(value: UUID) extends AnyVal
object SoftwareId {
  def fromString(value: String): Either[Throwable, SoftwareId] =
    Try(UUID.fromString(value)).toEither.map(SoftwareId.apply)
}
