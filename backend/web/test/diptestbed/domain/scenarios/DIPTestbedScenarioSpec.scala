package diptestbed.domain.scenarios

import akka.actor.{ActorSystem, PoisonPill}
import org.scalatest.{GivenWhenThen, Succeeded}
import akka.stream.Materializer
import akka.testkit.TestProbe
import cats.effect.IO
import io.circe.syntax._
import diptestbed.domain.Hardware
import diptestbed.domain.controllers.HardwareMessageSpec.createHardwareMessage
import diptestbed.domain.controllers.HardwareSpec.createHardware
import diptestbed.domain.controllers.DIPTestbedSpec
import diptestbed.domain.controllers.HomeControllerSpec._
import diptestbed.domain.controllers.UserControllerSpec._
import diptestbed.protocol._
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.DIPTestbedModule
import diptestbed.web.actors.HardwareMessageSubscriptionActor.subscribed
import diptestbed.web.controllers._

class DIPTestbedScenarioSpec extends DIPTestbedSpec with GivenWhenThen {
  lazy val module: DIPTestbedModule = module()
  implicit lazy val actorSystem: ActorSystem = module.actorSystem
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController
  lazy val userController: UserController = module.userController
  lazy val hardwareController: HardwareController = module.hardwareController
  lazy val hardwareMessageController: HardwareMessageController = module.hardwareMessageController

  "DIPTestbedScenario" - {
    "should succeed in running a game in a frisbee field" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = Then("Initially status should be empty")
        initialStatus <- getStatus(homeController)
        initialStatusCheck = initialStatus.shouldEqual(Right(Success(ServiceStatus.empty)))

        _ = And("A user w/ a generated id should be creatable")
        userPassword = "hunter2"
        userCreation <- createUser(userController, CreateUser("andrew", userPassword))
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

        _ = And("Finally the status should represent the changes")
        finalStatus <- getStatus(homeController)
        finalStatusCheck = finalStatus.shouldEqual(Right(Success(ServiceStatus(1, 1, 1))))

        assertions =
          initialStatusCheck ::
            userCreationCheck ::
            hardwareCreationCheck ::
            messageSubscriptionInitCheck ::
            hardwareMessageCreationCheck ::
            messageSubscriptionReceiveCheck ::
            finalStatusCheck ::
            Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}
