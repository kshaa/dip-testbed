package iotfrisbee.web.ioControls

import scala.concurrent.Await
import scala.concurrent.duration.DurationInt
import scala.util.Try
import akka.stream.Materializer
import cats.Monad
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import play.api.libs.circe.Circe
import play.api.mvc.{Action, AnyContent, BodyParser, Request}
import play.api.mvc._
import io.circe.Codec
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.ioControls.PipelineOps._

trait IOController extends Circe {
  import PipelineTypes._

  val effectMonad: Monad[IO] = Monad[IO]

  def cc: play.api.mvc.ControllerComponents

  def charset(result: Result): Option[String] =
    result.body.contentType match {
      case Some(s) if s.contains("charset=") => Some(s.split("; *charset=").drop(1).mkString.trim)
      case _                                 => None
    }

  // This method is bad and it makes me unhappy - https://i.imgur.com/8gvEZqx.jpg
  // (because of the global execution context use)
  def resultAsString(result: Result)(implicit materializer: Materializer): String = {
    import scala.concurrent.ExecutionContext.Implicits.global
    Await.result(result.body.consumeData.map(_.decodeString(charset(result).getOrElse("utf-8"))), 1.minute)
  }

  def reformatParseFailure(result: Result)(implicit materializer: Materializer): Result =
    Failure[String](resultAsString(result)).withHttpStatus(result.header.status)

  def formatHandlerFailure(throwable: Throwable): Result =
    Failure[String](throwable.getMessage).withHttpStatus(INTERNAL_SERVER_ERROR)

  def IOActionParsed[A](
    bodyParser: BodyParser[A],
  )(handler: Request[A] => PipelineRes[IO])(implicit iort: IORuntime, materializer: Materializer): Action[A] =
    cc.actionBuilder.async[A]({
      BodyParser.apply(bodyParser.andThen(_.map(_.leftMap(reformatParseFailure(_)))(iort.compute)))
    })(
      handler(_).merge
        .map(Try(_).fold(formatHandlerFailure, success => success))
        .unsafeToFuture(),
    )

  def IOActionAny(
    handler: Request[AnyContent] => PipelineRes[IO],
  )(implicit iort: IORuntime, materializer: Materializer): Action[AnyContent] =
    IOActionParsed[AnyContent](BodyParsers.utils.ignore(AnyContentAsEmpty: AnyContent))(handler)

  def IOActionJSON[A: Codec](
    handler: Request[A] => PipelineRes[IO],
  )(implicit iort: IORuntime, materializer: Materializer): Action[A] =
    IOActionParsed(circe.json[A])(handler)

}
