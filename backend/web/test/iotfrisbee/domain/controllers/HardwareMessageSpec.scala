package iotfrisbee.domain.controllers

import org.scalatest._
import play.api.mvc.AnyContent
import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import cats.implicits._
import io.circe._
import io.circe.syntax.EncoderOps
import iotfrisbee.domain.controllers.HardwareMessageSpec._
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.domain.controllers.HardwareSpec._
import iotfrisbee.domain.{HardwareMessage, HardwareMessageId}
import iotfrisbee.domain.controllers.IotFrisbeeSpec.exchangeJSON
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.{HardwareController, HardwareMessageController, UserController}

class HardwareMessageSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val userController: UserController = module.userController
  lazy val hardwareController: HardwareController = module.hardwareController
  lazy val hardwareMessageController: HardwareMessageController = module.hardwareMessageController

  "HardwareMessageController" - {
    "should be valid" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = When("A user w/ a generated id is created")
        userCreation <- createUser(userController, CreateUser("janisberzins"))
        user = userCreation.map(_.value).toOption.get

        _ = And("Their hardware w/ a generated id is created")
        hardwareCreation <- createHardware(hardwareController, CreateHardware("adafruit", user.id))
        hardware = hardwareCreation.map(_.value).toOption.get

        _ = Then("Hardware message w/ a generated id should be creatable")
        hardwareMessageCreate <- createHardwareMessage(
          hardwareMessageController,
          CreateHardwareMessage("debug-bluetooth-strength", "95.2", hardware.id),
        )
        hardwareMessage = hardwareMessageCreate.map(_.value).toOption
        hardwareMessageCreateCheck =
          hardwareMessageCreate
            .map(_.value)
            .map(m => (m.messageType, m.message, m.hardwareId))
            .shouldEqual(Right("debug-bluetooth-strength", "95.2", hardware.id))

        _ = Then("Hardware should be retrievable by a generated id")
        hardwareMessageGet <-
          hardwareMessage
            .traverse(m => getHardwareMessage(hardwareMessageController, m.id).map(_.toOption))
            .map(_.flatten)
        hardwareMessageGetCheck =
          hardwareMessageGet.map(_.value.messageType).shouldEqual(Some("debug-bluetooth-strength"))

        _ = And("Hardware should be listed")
        hardwareListing <- getHardwareMessages(hardwareMessageController)
        hardwareListingCheck =
          hardwareListing.map(_.value.map(_.messageType)).shouldEqual(Right("debug-bluetooth-strength" :: Nil))

        assertions = hardwareMessageCreateCheck :: hardwareMessageGetCheck :: hardwareListingCheck :: Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}

object HardwareMessageSpec {
  def createHardwareMessage(
    hardwareMessageController: HardwareMessageController,
    createHardwareMessage: CreateHardwareMessage,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[HardwareMessage]]] =
    exchangeJSON[CreateHardwareMessage, Success[HardwareMessage]](
      hardwareMessageController.createHardwareMessage,
      Some(createHardwareMessage.asJson),
    )

  def getHardwareMessages(
    hardwareMessageController: HardwareMessageController,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[List[HardwareMessage]]]] =
    exchangeJSON[AnyContent, Success[List[HardwareMessage]]](hardwareMessageController.getHardwareMessages, None)

  def getHardwareMessage(
    hardwareMessageController: HardwareMessageController,
    hardwareMessageId: HardwareMessageId,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[HardwareMessage]]] =
    exchangeJSON[AnyContent, Success[HardwareMessage]](
      hardwareMessageController.getHardwareMessage(hardwareMessageId),
      None,
    )
}
