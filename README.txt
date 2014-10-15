`PiCloud <http://www.picloud.com>`_ is a cloud-computing platform that integrates into the Python Programming Language. It enables you to leverage the computing power of Amazon Web Services without having to manage, maintain, or configure virtual servers.

When using this Python library known as *cloud*, PiCloud will integrate seamlessly into your existing code base. To offload the execution of a function to our servers, all you must do is pass your desired function into the *cloud* library. PiCloud will run the function on its high-performance cluster. As you run more functions, our cluster auto-scales to meet your computational needs. 

Before using this package, you will need to sign up a `PiCloud <http://www.picloud.com>`_ account.

The *cloud* library also features a simulator, which can be used without a PiCloud account.  The simulator uses the  `multiprocessing <http://docs.python.org/library/multiprocessing.html>`_ library to create a stripped down version of the PiCloud service.  This simulated service can then run jobs locally across all CPU cores.

Quick command-line example::
  
	>>> import cloud
	>>> def square(x):
	...     return x*x
	...     
	>>> jid = cloud.call(square,3)  #square(3) evaluated on PiCloud
	>>> cloud.result(jid)
	9

Full package documentation is available at http://docs.picloud.com.  Some dependencies may be required depending on your platform and Python version; see INSTALL for more information.

