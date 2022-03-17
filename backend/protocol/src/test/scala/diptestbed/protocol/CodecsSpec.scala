package diptestbed.protocol

import org.scalatest.matchers.should.Matchers
import org.scalatest.freespec.AnyFreeSpec
import io.circe.parser._
import io.circe.syntax._
import diptestbed.domain._
import diptestbed.protocol.DomainCodecs._
import diptestbed.protocol.HardwareSerialMonitorCodecs._
import diptestbed.protocol.HardwareControlCodecs._
import diptestbed.protocol.WebResult._


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

  "hardware control upload request messages should encode and decode" in {
    // {"command":"uploadSoftwareRequest","payload":{"softwareId":"16d7ce54-2d10-11ec-a35e-d79560b12f04"}}
    val softwareUUID = "16d7ce54-2d10-11ec-a35e-d79560b12f04"
    val serialized = "{\"command\":\"uploadSoftwareRequest\",\"payload\":{\"softwareId\":\"" + softwareUUID + "\"}}"
    val softwareId = SoftwareId.fromString(softwareUUID).toOption.get
    val unserialized: HardwareControlMessageNonBinary = HardwareControlMessageExternalNonBinary.UploadSoftwareRequest(softwareId)
    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareControlMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

  "hardware control upload result messages should encode and decode" in {
    // {"command":"uploadSoftwareResult","payload":{"error":null}}
    // {"command":"uploadSoftwareResult","payload":{"error":"lp0 on fire"}}
    val serialized = "{\"command\":\"uploadSoftwareResult\",\"payload\":{\"error\":null}}"
    val unserialized: HardwareControlMessageNonBinary = HardwareControlMessageExternalNonBinary.UploadSoftwareResult(None)
    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareControlMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

  "hardware monitor request messages should encode and decode" in {
    // {"command":"serialMonitorRequest","payload":{"serialConfig":null}}
    // {"command":"serialMonitorRequest","payload":{"serialConfig":{"receiveSize":115200,"baudrate":1,"timeout":0.3}}}
    val serialized = "{" +
      "\"command\":\"serialMonitorRequest\"," +
      "\"payload\":{" +
      "\"serialConfig\":" +
      "{\"receiveSize\":115200,\"baudrate\":1,\"timeout\":0.3" +
      "}" +
      "}" +
      "}"
    val unserialized: HardwareControlMessageNonBinary =
      HardwareControlMessageExternalNonBinary.SerialMonitorRequest(Some(SerialConfig(115200, 1, 0.3f)))

    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareControlMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

  "hardware monitor result messages should encode and decode" in {
    // {"command":"serialMonitorResult","payload":{"error":null}}
    // {"command":"serialMonitorResult","payload":{"error":"lp0 on fire"}}
    val serialized = "{\"command\":\"serialMonitorResult\",\"payload\":{\"error\":null}}"
    val unserialized: HardwareControlMessageNonBinary = HardwareControlMessageExternalNonBinary.SerialMonitorResult(None)

    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareControlMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

  "hardware control monitor unavailable messages should encode and decode" in {
    // {"command":"monitorUnavailable","payload":{"reason":"lp0 on fire"}}
    val serialized = "{\"command\":\"monitorUnavailable\",\"payload\":{\"reason\":\"lp0 on fire\"}}"
    val unserialized: HardwareSerialMonitorMessageNonBinary = HardwareSerialMonitorMessageNonBinary.MonitorUnavailable("lp0 on fire")
    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareSerialMonitorMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

  "hardware control auth messages should encode and decode" in {
    // {"command":"authRequest","payload":{"username":"user","password":"pass"}}
    val serialized = "{\"command\":\"authRequest\",\"payload\":{\"username\":\"user\",\"password\":\"pass\"}}"
    val unserialized: HardwareControlMessageNonBinary = HardwareControlMessageExternalNonBinary.AuthRequest("user", "pass")
    unserialized.asJson.noSpaces.shouldEqual(serialized)
    decode[HardwareControlMessageNonBinary](serialized).shouldEqual(Right(unserialized))
  }

}
