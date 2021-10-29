package diptestbed.protocol

import io.circe.Json

case class NamedMessage(command: String, payload: Json)
