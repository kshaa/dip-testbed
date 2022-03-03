package diptestbed.web.sird

import java.util.UUID
import play.api.routing.sird.PathBindableExtractor

object Binders {
  val uuid: PathBindableExtractor[UUID] = new PathBindableExtractor[UUID]
}
