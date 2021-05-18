package iotfrisbee.domain.controllers

import akka.util.Timeout
import cats.effect.testing.scalatest.AsyncIOSpec
import iotfrisbee.web.IotFrisbeeModule
import org.scalatest.TestSuite
import org.scalatest.freespec.AsyncFreeSpecLike
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.play.components.OneAppPerSuiteWithComponents
import play.api.{BuiltInComponents, Configuration}
import scala.concurrent.duration.DurationInt

trait IotFrisbeeSpec
    extends TestSuite
    with OneAppPerSuiteWithComponents
    with AsyncFreeSpecLike
    with AsyncIOSpec
    with Matchers {
  implicit def defaultAwaitTimeout: Timeout = 60.seconds
  override def components: BuiltInComponents = module
  lazy val testSpecName: String = this.getClass.getSimpleName.toLowerCase()
  lazy val module = new IotFrisbeeModule(
    context.copy(initialConfiguration =
      Configuration(
        "iotfrisbee.test.enabled" -> true,
        "iotfrisbee.test.name" -> testSpecName,
      ).withFallback(context.initialConfiguration),
    ),
  )
}
