package iotfrisbee.domain.controllers

import iotfrisbee.web.controllers.HomeController
import iotfrisbee.web.iocontroller.PipelineOps._
import scala.concurrent.Future
import play.api.test.{FakeRequest, Helpers}
import io.circe.syntax._
import iotfrisbee.protocol.Codecs._
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
          .map(x => x.shouldEqual(ServiceStatus(1, 0).asJson.toString))
    }
  }
}
