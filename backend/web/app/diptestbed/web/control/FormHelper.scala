package diptestbed.web.control

import play.api.data.Forms.{optional, text}
import play.api.data.Mapping

object FormHelper {
  def optionalBoolean: Mapping[Boolean] = optional(text).transform(_.contains("on"), if (_) Some("on") else None)
}
