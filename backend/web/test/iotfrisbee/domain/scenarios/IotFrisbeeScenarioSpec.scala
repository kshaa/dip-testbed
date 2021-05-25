package iotfrisbee.domain.scenarios

import org.scalatest.{GivenWhenThen, Succeeded}
import akka.stream.Materializer
import cats.effect.IO
import iotfrisbee.domain.controllers.IotFrisbeeSpec
import iotfrisbee.domain.controllers.HomeControllerSpec._
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.protocol.messages.home.ServiceStatus
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.protocol.messages.users.CreateUser
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.{HomeController, UserController}

class IotFrisbeeScenarioSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController
  lazy val userController: UserController = module.userController

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

        _ = And("Finally the status should represent the changes")
        finalStatus <- IO(println("test4")) *> getStatus(homeController)
        finalStatusCheck = finalStatus.shouldEqual(Right(Success(ServiceStatus(1, 0))))

        assertions = initialStatusCheck :: userCreationCheck :: finalStatusCheck :: Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}
