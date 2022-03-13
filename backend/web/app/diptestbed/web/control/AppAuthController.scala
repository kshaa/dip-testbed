package diptestbed.web.control

import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import diptestbed.database.services.UserService
import diptestbed.domain.{DIPTestbedConfig, HashedPassword, User}
import diptestbed.web.ioControls._
import play.api.data.Form
import play.api.data.Forms.{text, tuple}
import play.api.i18n.Messages
import play.api.mvc._
import play.mvc.Security

class AppAuthController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO],
)(implicit
  ioRuntime: IORuntime,
  messages: Messages)
  extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {

  def authForm(error: String, validation: (String, String) => Boolean): Form[(String, String)] = Form[(String, String)](
    tuple(
      "username" -> text,
      "password" -> text
    ) verifying (error, {
      case (username, password) => validation(username, password)
    })
  )

  def validateLogin(username: String, password: String): Option[User] = {
    AuthController.validateLogin(username, password, userService, appConfig)
      .map(_.toOption.flatten).unsafeRunSync()
  }

  val loginForm: Form[(String, String)] =
    authForm("Invalid email or password", validateLogin(_, _).isDefined)

  def login: Action[AnyContent] =
    Action { implicit request =>
      contextUser.unsafeRunSync() match {
        case None => Ok(diptestbed.web.views.html.auth(
          appConfig, loginForm, "Login", appConfig.withAppPath("/login")))
        case Some(_) => Redirect(appConfig.withAppPath("/"))
      }
    }

  def loginRequest: Action[AnyContent] =
    Action { implicit request =>
      loginForm.bindFromRequest.fold(
        formWithErrors => BadRequest(diptestbed.web.views.html.auth(
          appConfig, formWithErrors, "Login", appConfig.withAppPath("/login"))),
        { case (username, _) =>
          Redirect(appConfig.withAppPath("/")).withSession(Security.USERNAME.toString -> username) }
      )
    }

  def createUser(username: String, password: String): Option[User] = {
    AuthController.validateRegistration(username, password, userService, appConfig)
      .map(_.toOption.flatten).unsafeRunSync()
  }

  val registerForm: Form[(String, String)] =
    authForm("Failed to register", createUser(_, _).isDefined)

  def register: Action[AnyContent] =
    Action { implicit request =>
      contextUser.unsafeRunSync() match {
        case None => Ok(diptestbed.web.views.html.auth(
          appConfig, registerForm, "Register", appConfig.withAppPath("/register")))
        case Some(_) => Redirect(appConfig.withAppPath("/"))
      }
    }

  def registerRequest: Action[AnyContent] =
    Action { implicit request =>
      registerForm.bindFromRequest.fold(
        formWithErrors => BadRequest(diptestbed.web.views.html.auth(
          appConfig, formWithErrors, "Register", appConfig.withAppPath("/register"))),
        { case (username, _) =>
          Redirect(appConfig.withAppPath("/")).withSession(Security.USERNAME.toString -> username) }
      )
    }

  def logout: Action[AnyContent] =
    Action { implicit request =>
      Redirect(appConfig.withAppPath("/")).withNewSession
    }

}
