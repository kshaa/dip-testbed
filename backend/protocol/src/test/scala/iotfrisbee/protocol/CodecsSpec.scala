package iotfrisbee.protocol

import org.scalatest.matchers.should.Matchers
import org.scalatest.freespec.AnyFreeSpec
import io.circe.parser._
import io.circe.syntax._
import iotfrisbee.domain.DomainTimeZoneId
import iotfrisbee.protocol.WebResult._
import iotfrisbee.protocol.Codecs._

class CodecsSpec extends AnyFreeSpec with Matchers {
  "hello message should have recipient with hello" in {
    val serialized: String = "{ \"hello\": \"world\" }"
    val unserialized: Hello = Hello("world")
    decode[Hello](serialized) === Right(unserialized)
    unserialized.asJson === serialized
  }

  "success web result message should encode and decode" in {
    val serialized: String = "{ \"success\": 42 }"
    val unserialized = Success(42)
    decode[Success[Integer]](serialized).shouldEqual(Right(unserialized))
    unserialized.asJson === serialized
  }

  "error web result message should encode and decode" in {
    val serialized: String = "{ \"failure\": \"message\" }"
    val unserialized = Failure("message")
    decode[Failure[String]](serialized).shouldEqual(Right(unserialized))
    unserialized.asJson === serialized
  }

  "domain time zone id should encode and decode" in {
    val timeZoneId = "Europe/Riga"
    val serialized: String = timeZoneId.asJson.toString()
    val unserialized = DomainTimeZoneId.fromString(timeZoneId).toOption.get
    decode[DomainTimeZoneId](serialized).shouldEqual(Right(unserialized))
    unserialized.asJson === serialized
  }
}
