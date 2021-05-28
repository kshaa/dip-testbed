package iotfrisbee.domain.controllers

import scala.concurrent.Future
import org.scalatest._
import akka.stream.Materializer
import akka.util.{ByteString, Timeout}
import cats.effect.IO
import cats.implicits.toTraverseOps
import io.circe._
import io.circe.parser._
import io.circe.syntax.EncoderOps
import play.api.mvc.Headers
import play.api.test.Helpers.CONTENT_TYPE
import play.api.test.{FakeRequest, Helpers}
import iotfrisbee.domain.{User, UserId}
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.UserController
import iotfrisbee.web.ioControls.PipelineOps._

class UserControllerSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val userController: UserController = module.userController

  "UserController" - {
    "should be valid" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = Then("A user w/ a generated id should be creatable")
        userCreation <- createUser(userController, CreateUser("john"))
        user = userCreation.map(_.value).toOption
        userCreationCheck = userCreation.map(_.value.username).shouldEqual(Right("john"))

        _ = Then("A user w/ a duplicate username should be forbidden")
        userDuplicateCreation <- createUser(userController, CreateUser("john"))
        userDuplicateCreationCheck = userDuplicateCreation.isLeft.shouldBe(true)

        _ = And("A user should be retrievable by a generated id")
        userGet <- user.traverse(u => getUser(userController, u.id).map(_.toOption)).map(_.flatten)
        userGetCheck = userGet.map(_.value.username).shouldEqual(Some("john"))

        _ = And("A user should be listed")
        userListing <- getUsers(userController)
        userListingCheck = userListing.map(_.value.map(_.username)).shouldEqual(Right("john" :: Nil))

        assertions = userCreationCheck :: userDuplicateCreationCheck :: userGetCheck :: userListingCheck :: Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}

object UserControllerSpec {
  def createUser(
    userController: UserController,
    createUser: CreateUser,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[User]]] =
    userController.createUser
      .apply(FakeRequest().withHeaders(Headers(CONTENT_TYPE -> "application/json")))
      .run(ByteString(createUser.asJson.toString()))
      .asIO
      .map(x => Helpers.contentAsString(Future.successful(x)))
      .map(x => decode[Success[User]](x))

  def getUsers(
    userController: UserController,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[List[User]]]] =
    userController.getUsers
      .apply(FakeRequest().withHeaders(Headers(CONTENT_TYPE -> "application/json")))
      .asIO
      .map(x => Helpers.contentAsString(Future.successful(x)))
      .map(x => decode[Success[List[User]]](x))

  def getUser(
    userController: UserController,
    userId: UserId,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[User]]] =
    userController
      .getUser(userId)
      .apply(FakeRequest())
      .asIO
      .map(x => Helpers.contentAsString(Future.successful(x)))
      .map(x => decode[Success[User]](x))
}
