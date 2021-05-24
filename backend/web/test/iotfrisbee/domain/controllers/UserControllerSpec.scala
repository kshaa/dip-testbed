package iotfrisbee.domain.controllers

import scala.concurrent.Future
import akka.stream.Materializer
import akka.util.ByteString
import cats.effect.IO
import io.circe.parser._
import io.circe.syntax.EncoderOps
import org.scalatest.Assertion
import play.api.mvc.Headers
import play.api.test.Helpers.CONTENT_TYPE
import play.api.test.{FakeRequest, Helpers}
import iotfrisbee.domain.User
import iotfrisbee.protocol.Codecs.Domain._
import iotfrisbee.protocol.Codecs.Http._
import iotfrisbee.protocol.Codecs.User._
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.protocol.messages.users.CreateUser
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.UserController
import iotfrisbee.web.iocontrols.PipelineOps._

class UserControllerSpec extends IotFrisbeeSpec {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val userController: UserController = module.userController

  "UserController#createUser" - {
    "should be valid" in {
      val userCreation = userController.createUser
        .apply(FakeRequest().withHeaders(Headers(CONTENT_TYPE -> "application/json")))
        .run(ByteString(CreateUser("john").asJson.toString()))
        .asIO

      val userCreationValidation: IO[Assertion] = userCreation
        .map(x => Helpers.contentAsString(Future.successful(x)))
        .map(x => decode[Success[User]](x).map(_.value.username))
        .map(x => x.shouldEqual(Right("john")))

      userCreationValidation
    }
  }
}
