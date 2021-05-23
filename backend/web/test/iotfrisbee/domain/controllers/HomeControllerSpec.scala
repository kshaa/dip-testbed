package iotfrisbee.domain.controllers

import scala.concurrent.Future
import play.api.test.{FakeRequest, Helpers}
import io.circe.parser._
import iotfrisbee.web.controllers.HomeController
import iotfrisbee.web.iocontroller.PipelineOps._
import iotfrisbee.protocol.Codecs.Web._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.protocol.messages.WebResult.Success
import iotfrisbee.protocol.messages.ServiceStatus

class HomeControllerSpec extends IotFrisbeeSpec {
  lazy val controller: HomeController = module().homeController

  "Home#index" - {
    "should be valid" in {
      controller.addUser("john").apply(FakeRequest()).asIO *>
        controller
          .status()
          .apply(FakeRequest())
          .asIO
          .map(x => Helpers.contentAsString(Future.successful(x)))
          .map(x =>
            decode[Success[ServiceStatus]](x)
              .shouldEqual(Right(Success(ServiceStatus(1, 0)))),
          )
    }
  }
}
