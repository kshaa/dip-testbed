package iotfrisbee.domain.controllers

import java.util.UUID
import org.scalatest._
import play.api.mvc.AnyContent
import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import cats.implicits._
import io.circe._
import io.circe.syntax.EncoderOps
import iotfrisbee.domain.controllers.HardwareSpec._
import iotfrisbee.domain.{Hardware, HardwareId, UserId}
import iotfrisbee.domain.controllers.IotFrisbeeSpec.exchangeJSON
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.{HardwareController, UserController}

class HardwareSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val userController: UserController = module.userController
  lazy val hardwareController: HardwareController = module.hardwareController

  "HardwareController" - {
    "should be valid" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = Then("Hardware wo/ an existing user should be impossible")
        ownerlessHardwareCreate <- createHardware[Failure[String]](
          hardwareController,
          CreateHardware("adafruit-nrf52-1", UserId(UUID.fromString("00000000-0000-0000-0000-000000000000"))),
        )
        ownerlessHardwareCreateCheck =
          ownerlessHardwareCreate
            .shouldEqual(Right(Failure("Owner with that id doesn't exist")))

        _ = When("A user w/ a generated id is created")
        userPassword = "hunter2"
        userCreation <- createUser(userController, CreateUser("janisberzins", userPassword))
        user = userCreation.map(_.value).toOption.get

        _ = Then("Hardware w/ a generated id should be creatable")
        hardwareCreate <- createHardware[Success[Hardware]](
          hardwareController,
          CreateHardware("adafruit-nrf52-1", user.id),
        )
        hardware = hardwareCreate.map(_.value).toOption
        hardwareCreateCheck =
          hardwareCreate
            .map(_.value)
            .map(h => (h.name, h.ownerId))
            .shouldEqual(Right("adafruit-nrf52-1", user.id))

        _ = Then("Hardware should be retrievable by a generated id")
        hardwareGet <- hardware.traverse(h => getHardware(hardwareController, h.id).map(_.toOption)).map(_.flatten)
        hardwareGetCheck = hardwareGet.map(_.value.name).shouldEqual(Some("adafruit-nrf52-1"))

        _ = And("Hardware should be listed")
        hardwareListing <- getHardwares(hardwareController)
        hardwareListingCheck = hardwareListing.map(_.value.map(_.name)).shouldEqual(Right("adafruit-nrf52-1" :: Nil))

        assertions =
          ownerlessHardwareCreateCheck ::
            hardwareCreateCheck ::
            hardwareGetCheck ::
            hardwareListingCheck ::
            Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}

object HardwareSpec {
  def createHardware[O: Decoder](
    hardwareController: HardwareController,
    createHardware: CreateHardware,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, O]] =
    exchangeJSON[CreateHardware, O](
      hardwareController.createHardware,
      Some(createHardware.asJson),
    )

  def getHardwares(
    hardwareController: HardwareController,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[List[Hardware]]]] =
    exchangeJSON[AnyContent, Success[List[Hardware]]](hardwareController.getHardwares, None)

  def getHardware(
    hardwareController: HardwareController,
    hardwareId: HardwareId,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[Hardware]]] =
    exchangeJSON[AnyContent, Success[Hardware]](hardwareController.getHardware(hardwareId), None)
}
