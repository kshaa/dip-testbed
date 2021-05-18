package iotfrisbee.protocol

import io.circe.parser._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.messages.Hello
import org.scalatest.freespec.AnyFreeSpec

class CodecsSpec extends AnyFreeSpec {
  "hello message should have recipient with hello" in {
    val hello = "{ \"hello\": \"world\" }"
    decode[Hello](hello) == Right(
      Hello("world"),
    )
  }
}
