package iotfrisbee.domain.controllers

import scala.concurrent.Future
import akka.stream.Materializer
import cats.effect.IO
import play.api.test.{FakeRequest, Helpers}
import play.api.mvc.Result
import io.circe.parser._
import org.scalatest.Assertion
import iotfrisbee.protocol.Codecs.Http._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.web.controllers.HomeController
import iotfrisbee.web.iocontrols.PipelineOps._
import iotfrisbee.protocol.messages.home.ServiceStatus
import iotfrisbee.protocol.messages.http.WebResult.Success
import iotfrisbee.web.IotFrisbeeModule

class HomeControllerSpec extends IotFrisbeeSpec {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val homeController: HomeController = module.homeController

  "HomeController#status" - {
    "should be valid" in {
      val status: IO[Result] = homeController.status().apply(FakeRequest()).asIO
      val statusValidation: IO[Assertion] = status
        .map(x => Helpers.contentAsString(Future.successful(x)))
        .map(x =>
          decode[Success[ServiceStatus]](x)
            .shouldEqual(Right(Success(ServiceStatus(0, 0)))),
        )

      statusValidation
    }
  }
}
