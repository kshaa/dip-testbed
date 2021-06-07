package iotfrisbee.domain.scenarios

import akka.actor.{ActorSystem, PoisonPill}
import org.scalatest.{GivenWhenThen, Succeeded}
import akka.stream.Materializer
import akka.testkit.TestProbe
import cats.effect.IO
import io.circe.syntax._
import iotfrisbee.domain.{DomainTimeZoneId, Hardware}
import iotfrisbee.domain.controllers.DiskGolfTrackSpec._
import iotfrisbee.domain.controllers.HardwareMessageSpec.createHardwareMessage
import iotfrisbee.domain.controllers.HardwareSpec.createHardware
import iotfrisbee.domain.controllers.IotFrisbeeSpec
import iotfrisbee.domain.controllers.HomeControllerSpec._
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.actors.HardwareMessageSubscriptionActor.subscribed
import iotfrisbee.web.controllers._

class IotFrisbeeScenarioSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val actorSystem: ActorSystem = module.actorSystem
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController
  lazy val userController: UserController = module.userController
  lazy val diskGolfTrackController: DiskGolfTrackController = module.diskGolfTrackController
  lazy val hardwareController: HardwareController = module.hardwareController
  lazy val hardwareMessageController: HardwareMessageController = module.hardwareMessageController

  "IotFrisbeeScenario" - {
    "should succeed in running a game in a frisbee field" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = Then("Initially status should be empty")
        initialStatus <- getStatus(homeController)
        initialStatusCheck = initialStatus.shouldEqual(Right(Success(ServiceStatus.empty)))

        _ = And("A user w/ a generated id should be creatable")
        userCreation <- createUser(userController, CreateUser("andrew"))
        userCreationCheck = userCreation.map(_.value.username).shouldEqual(Right("andrew"))
        user = userCreation.map(_.value).toOption.get

        _ = And("Users' hardware w/ a generated id should be creatable")
        hardwareCreation <- createHardware[Success[Hardware]](hardwareController, CreateHardware("adafruit", user.id))
        hardwareCreationCheck = hardwareCreation.map(_.value.name).shouldEqual(Right("adafruit"))
        hardware = hardwareCreation.map(_.value).toOption.get

        _ = And("A listener subscribes to hardware messages")
        messageSubscriber = TestProbe()
        messageSubscription =
          actorSystem.actorOf(hardwareMessageController.hardwareMessageSubscription(messageSubscriber.ref, hardware.id))
        messageSubscriptionInitCheck = messageSubscriber.expectMsg(subscribed).shouldEqual(subscribed)

        _ = And("Hardware message w/ a generated id should be creatable")
        hardwareMessageCreation <- createHardwareMessage(
          hardwareMessageController,
          CreateHardwareMessage("debug-sensor", "moist".asJson, hardware.id),
        )
        hardwareMessageCreationCheck = hardwareMessageCreation.map(_.value.message).shouldEqual(Right("moist".asJson))
        hardwareMessage = hardwareMessageCreation.map(_.value).toOption.get

        _ = Then("Hardware message subscriber should receive notification")
        messageSubscriptionReceiveCheck =
          messageSubscriber.expectMsg(hardwareMessage.asJson.toString).shouldEqual(hardwareMessage.asJson.toString)
        _ = messageSubscription ! PoisonPill

        _ = And("A disk golf track w/ a generated id should be creatable")
        rigaTimeZoneId = DomainTimeZoneId.fromString("Europe/Riga").toOption.get
        diskGolfTrackCreation <- createDiskGolfTrack(
          diskGolfTrackController,
          CreateDiskGolfTrack(user.id, "Talsi", rigaTimeZoneId),
        )
        diskGolfTrack = diskGolfTrackCreation.map(_.value).toOption.get
        diskGolfTrackCheck =
          diskGolfTrackCreation
            .map(t => (t.value.name, t.value.timezoneId))
            .shouldEqual(Right("Talsi", rigaTimeZoneId))

        _ = And("Finally the status should represent the changes")
        finalStatus <- getStatus(homeController)
        finalStatusCheck = finalStatus.shouldEqual(Right(Success(ServiceStatus(1, 1, 1, 1, 0))))

        assertions =
          initialStatusCheck ::
            userCreationCheck ::
            hardwareCreationCheck ::
            messageSubscriptionInitCheck ::
            hardwareMessageCreationCheck ::
            messageSubscriptionReceiveCheck ::
            diskGolfTrackCheck ::
            finalStatusCheck ::
            Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}
