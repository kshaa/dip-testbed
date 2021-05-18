package iotfrisbee.domain.controllers

import cats.effect.IO
import iotfrisbee.web.controllers.HomeController

import scala.concurrent.Future
import play.api.test.{FakeRequest, Helpers}

class HomeControllerSpec extends IotFrisbeeSpec {
  lazy val controller: HomeController = module.homeController
  "Home#index" - {
    "should be valid" in {
      IO.fromFuture(IO(controller.addUser("john").apply(FakeRequest()))) *>
        IO.fromFuture(IO(controller.status().apply(FakeRequest())))
          .map(x => Helpers.contentAsString(Future.successful(x)))
          .map(x => x.shouldEqual("2"))
    }
  }
}
