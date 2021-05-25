package iotfrisbee.domain.scenarios

import org.scalatest.{GivenWhenThen, Succeeded}
import akka.stream.Materializer
import cats.effect.IO
import iotfrisbee.domain.DomainTimeZoneId
import iotfrisbee.domain.controllers.DiskGolfTrackSpecControllerSpec.createDiskGolfTrack
import iotfrisbee.domain.controllers.IotFrisbeeSpec
import iotfrisbee.domain.controllers.HomeControllerSpec._
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.protocol.messages.diskGolfTrack.CreateDiskGolfTrack
import iotfrisbee.protocol.messages.home.ServiceStatus
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.protocol.messages.user.CreateUser
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers._

class IotFrisbeeScenarioSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController
  lazy val userController: UserController = module.userController
  lazy val diskGolfTrackController: DiskGolfTrackController = module.diskGolfTrackController

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
        finalStatusCheck = finalStatus.shouldEqual(Right(Success(ServiceStatus(1, 1))))

        assertions = initialStatusCheck :: userCreationCheck :: diskGolfTrackCheck :: finalStatusCheck :: Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}
