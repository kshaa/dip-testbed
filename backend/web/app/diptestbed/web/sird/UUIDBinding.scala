package diptestbed.web.sird

import java.util.UUID
import play.api.mvc.PathBindable
import play.api.routing.sird.PathBindableExtractor

object UUIDBinding {
  val bindable: PathBindable[UUID] = new PathBindable[UUID] {
    override def bind(key: String, value: String): Either[String, UUID] = ???
    override def unbind(key: String, value: UUID): String = ???
  }

  val uuid = new PathBindableExtractor[UUID]
}
